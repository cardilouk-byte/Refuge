import re
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from finance.models import Invoice

from accounts.models import User
from accounts.views import direction_required, staff_required, teaching_staff_required
from academics.models import ClassRoom, Period
from students.models import Student

from .forms import CarnetSettingsForm
from .models import CarnetSettings, Grade

User = get_user_model()

CYCLE_LABELS = ["PREMYE SYIK", "DEZYEM SYIK", "TWAZYEM SYIK", "KATRIYEM SYIK", "SENKYEM SYIK", "SIZYEM SYIK"]


def _decision(avg):
    if avg is None:
        return "Pa gen nòt", "secondary"
    if avg >= 10:
        return "ADMIS", "success"
    if avg >= 8:
        return "ADMIS — AVÈTISMAN", "warning"
    if avg >= 5:
        return "REDOBLE", "warning"
    return "ECHOUE — REDOUBLE", "danger"


def _accessible_students(user):
    if not user.is_authenticated:
        return Student.objects.none()
    if user.is_teaching_staff or user.is_staff:
        return Student.objects.all()
    if user.role == User.Role.ELEVE:
        st = getattr(user, "student_profile", None)
        return Student.objects.filter(pk=st.pk) if st else Student.objects.none()
    if user.role == User.Role.PARENT:
        return Student.objects.filter(parentstudent__parent__user=user)
    return Student.objects.none()


def _get_student_for_view(request, student_pk):
    student = get_object_or_404(Student.objects.select_related("classroom__level__cycle"), pk=student_pk)
    if not _accessible_students(request.user).filter(pk=student.pk).exists():
        raise PermissionDenied
    return student


def _bulletin_data(student, period):
    classroom = student.classroom
    rows = []
    total_points = 0
    total_coef = 0
    if classroom:
        for cs in classroom.subjects.select_related("subject").order_by("subject__name"):
            avg = Grade.subject_average(student, cs, period)
            pts = round(float(avg) * cs.coefficient, 2) if avg is not None else None
            if avg is not None:
                total_points += float(avg) * cs.coefficient
                total_coef += cs.coefficient
            grades = Grade.objects.filter(student=student, class_subject=cs, period=period)
            notes = [{"kind": g.get_kind_display(), "score": g.score} for g in grades]
            rows.append({"cs": cs, "avg": avg, "points": pts, "notes": notes})
    moy = round(total_points / total_coef, 2) if total_coef else None
    decision, tone = _decision(moy)
    rank = None
    out_of = 0
    if classroom:
        ranking = Grade.class_ranking(classroom, period)
        out_of = len(ranking)
        for r, s, a in ranking:
            if s.pk == student.pk:
                rank = r
                break
    return {"rows": rows, "moy": moy, "moy_10": round(moy / 2, 2) if moy is not None else None,
            "rank": rank, "out_of": out_of, "decision": decision, "tone": tone}


@login_required
def class_list(request):
    if not (request.user.is_teaching_staff or request.user.is_staff):
        return redirect("grades:bulletin_home")
    classrooms = ClassRoom.objects.select_related("level", "school_year").order_by("school_year__label", "level__order", "section")
    for c in classrooms:
        c.nb_students = c.students.filter(status="ACTIF").count()
    return render(request, "grades/class_list.html", {"classrooms": classrooms})


@teaching_staff_required
def note_saisie(request, classroom_pk):
    classroom = get_object_or_404(ClassRoom.objects.select_related("level", "school_year"), pk=classroom_pk)
    periods = Period.objects.filter(school_year=classroom.school_year).order_by("order")
    subjects = classroom.subjects.select_related("subject").order_by("subject__name")

    period_id = request.GET.get("periyod") or request.POST.get("periyod")
    period = periods.filter(pk=period_id).first() if period_id else periods.order_by("-order").first()

    cs_id = request.GET.get("matye") or request.POST.get("matye")
    cs = subjects.filter(pk=cs_id).first() if cs_id else None

    kind = request.POST.get("tip") or request.GET.get("tip") or Grade.Kind.DEVOIR
    if kind not in Grade.Kind.values:
        kind = Grade.Kind.DEVOIR

    students = list(classroom.students.filter(status="ACTIF").order_by("last_name", "first_name"))
    existing = {}
    if period and cs:
        existing = {
            g.student_id: g
            for g in Grade.objects.filter(class_subject=cs, period=period, kind=kind, student__in=students)
        }

    if request.method == "POST" and period and cs:
        errors = []
        values = []
        to_delete = []
        for st in students:
            raw = request.POST.get(f"note_{st.pk}", "").strip()
            if raw == "":
                if st.pk in existing:
                    to_delete.append(existing[st.pk])
                continue
            try:
                score = Decimal(str(raw).replace(",", "."))
            except (InvalidOperation, ValueError):
                errors.append(f"{st.full_name}: « {raw} » pa se yon nòt valid.")
                continue
            if score < 0 or score > 20:
                errors.append(f"{st.full_name}: nòt {score} dwe ant 0 ak 20.")
                continue
            values.append((st, score))
        if errors:
            messages.error(request, "Nòt pa sove — gen erè: " + " | ".join(errors))
        else:
            for st, score in values:
                Grade.objects.update_or_create(
                    student=st, class_subject=cs, period=period, kind=kind,
                    defaults={"score": score, "entered_by": request.user},
                )
            for g in to_delete:
                g.delete()
            messages.success(request, f"{len(values)} nòt sove pou {cs} — {period.name} ({kind}).")
            return redirect(f"{request.path}?periyod={period.pk}&matye={cs.pk}&tip={kind}")

    return render(
        request,
        "grades/classroom.html",
        {
            "classroom": classroom,
            "periods": periods,
            "subjects": subjects,
            "period": period,
            "cs": cs,
            "kind": kind,
            "kinds": Grade.Kind.choices,
            "students": students,
            "existing": existing,
        },
    )


def _bulletin_locked(request, student):
    if request.user.is_staff:
        return None
    is_guardian = (
        getattr(request.user, "student_profile", None) is not None
        or Student.objects.filter(parentstudent__parent__user=request.user).exists()
    )
    if not is_guardian:
        return None
    unpaid = Invoice.objects.filter(student=student).exclude(status=Invoice.Status.PAYE).exists()
    if unpaid:
        return render(request, "grades/bulletin_locked.html", {"student": student})
    return None


@login_required
def bulletin_home(request):
    user = request.user
    if user.is_teaching_staff or user.is_staff:
        return redirect("grades:class_list")
    if user.role == User.Role.ELEVE:
        st = getattr(user, "student_profile", None)
        if st:
            return redirect("grades:bulletin_student", st.pk)
        return render(request, "grades/no_bulletin.html")
    students = _accessible_students(user)
    return render(request, "grades/parent_children.html", {"students": students})


@direction_required
def carnet_settings(request):
    carnet = CarnetSettings.load()
    if request.method == "POST":
        form = CarnetSettingsForm(request.POST, instance=carnet)
        if form.is_valid():
            form.save()
            messages.success(request, "Mod\u00e8l karn\u00e8 a sove. Chak nouvo karn\u00e8 pral s\u00e8vi ak t\u00e8 sa yo.")
            return redirect("grades:carnet_settings")
        messages.error(request, "Gen yon er\u00e8 nan f\u00f2m nan.")
    else:
        form = CarnetSettingsForm(instance=carnet)
    return render(request, "grades/carnet_settings.html", {"form": form, "titre": "Mod\u00e8l Karn\u00e8"})


def _is_official_level(level_name):
    lvl = re.sub(r"[\s.]", "", (level_name or "").lower())
    return "ns4" in lvl or lvl[:2] in ("9e", "9\u00e8")


@login_required
def carnet_print(request, student_pk):
    student = _get_student_for_view(request, student_pk)
    carnet = CarnetSettings.load()
    classroom = student.classroom
    sheets = []
    officials = []
    chart_labels = []
    chart_data = []
    is_official = False
    annual_moy = None
    annual_decision = "Pa gen n\u00f2t"
    if classroom:
        periods = list(Period.objects.filter(school_year=classroom.school_year).order_by("order"))
        subjects = list(
            classroom.subjects.select_related("subject", "teacher", "teacher__user").order_by("subject__name")
        )
        if periods:
            points = 0
            count = 0
            for i, p in enumerate(periods):
                rows = []
                st_points = 0.0
                st_coef = 0
                cl_points = 0.0
                cl_coef = 0
                for cs in subjects:
                    avg = Grade.subject_average(student, cs, p)
                    cls_avg = Grade.objects.filter(class_subject=cs, period=p).aggregate(a=Avg("score"))["a"]
                    if cls_avg is not None:
                        cl_points += float(cls_avg) * cs.coefficient
                        cl_coef += cs.coefficient
                    if avg is not None:
                        st_points += float(avg) * cs.coefficient
                        st_coef += cs.coefficient
                    rows.append({
                        "cs": cs,
                        "avg": avg,
                        "total": round(float(avg) * cs.coefficient, 2) if avg is not None else None,
                        "cls_avg": cls_avg,
                    })
                moy = round(st_points / st_coef, 2) if st_coef else None
                cl_moy = round(cl_points / cl_coef, 2) if cl_coef else None
                rank = None
                out_of = 0
                ranking = Grade.class_ranking(classroom, p)
                out_of = len(ranking)
                for r, s, a in ranking:
                    if s.pk == student.pk:
                        rank = r
                        break
                decision, tone = _decision(moy)
                sheets.append({
                    "period": p,
                    "label": CYCLE_LABELS[i] if i < len(CYCLE_LABELS) else p.name.upper(),
                    "rows": rows,
                    "moy": moy,
                    "cls_moy": cl_moy,
                    "rank": rank,
                    "out_of": out_of,
                    "decision": decision,
                    "tone": tone,
                })
                if moy is not None:
                    points += moy
                    count += 1
            if count:
                annual_moy = round(points / count, 2)
                annual_decision, _tone = _decision(annual_moy)
        is_official = _is_official_level(classroom.level.name)
        if is_official:
            for cs in subjects:
                g = Grade.latest_exam(student, cs)
                score = g.score if g else None
                officials.append({"cs": cs, "score": score, "teacher": cs.teacher})
                if score is not None:
                    chart_labels.append(cs.subject.name)
                    chart_data.append(float(score))
    return render(
        request,
        "grades/carnet_print.html",
        {
            "carnet": carnet,
            "student": student,
            "classroom": classroom,
            "sheets": sheets,
            "annual_moy": annual_moy,
            "annual_decision": annual_decision,
            "is_official": is_official,
            "officials": officials,
            "chart_labels": chart_labels,
            "chart_data": chart_data,
            "show_graph": carnet.show_graph,
            "titre": "Karn\u00e8 \u2014 " + student.full_name,
        },
    )


@teaching_staff_required
def honour(request):
    classrooms = ClassRoom.objects.select_related("level", "school_year").order_by(
        "school_year__label", "level__order", "section"
    )
    periods = Period.objects.order_by("-order")[:12]
    classroom_id = request.GET.get("klas")
    period_id = request.GET.get("periyod")

    honoured = []
    if period_id:
        period = Period.objects.filter(pk=period_id).first()
    else:
        period = periods.first() if periods else None
    if period:
        targets = [c for c in classrooms if not classroom_id or str(c.pk) == classroom_id]
        rows = []
        for classroom in targets:
            for rank, student, avg in Grade.class_ranking(classroom, period):
                if avg >= 10:
                    rows.append({"student": student, "avg": avg, "classroom": classroom})
        rows.sort(key=lambda row: row["avg"], reverse=True)
        for i, row in enumerate(rows[:10], start=1):
            row["rank"] = i
            honoured.append(row)
    return render(
        request,
        "grades/honour.html",
        {
            "classrooms": classrooms,
            "periods": periods,
            "f_classroom": classroom_id or "",
            "f_period": period_id or (str(period.pk) if period else ""),
            "honoured": honoured,
            "titre": "Tablo don\u00e8",
        },
    )


@teaching_staff_required
def bulletin_class(request, classroom_pk):
    classroom = get_object_or_404(ClassRoom.objects.select_related("level", "school_year"), pk=classroom_pk)
    periods = Period.objects.filter(school_year=classroom.school_year).order_by("order")
    period_id = request.GET.get("periyod")
    period = periods.filter(pk=period_id).first() if period_id else periods.order_by("-order").first()
    ranking = Grade.class_ranking(classroom, period) if period else []
    ranked = []
    for r, s, a in ranking:
        dec, tone = _decision(a)
        ranked.append({"rank": r, "student": s, "avg": a, "avg_10": round(a / 2, 2), "decision": dec, "tone": tone})
    return render(
        request,
        "grades/bulletin_class.html",
        {"classroom": classroom, "periods": periods, "period": period, "ranked": ranked},
    )


@login_required
def bulletin_student(request, student_pk):
    student = _get_student_for_view(request, student_pk)
    locked = _bulletin_locked(request, student)
    if locked:
        return locked
    periods = Period.objects.filter(school_year=student.classroom.school_year).order_by("order") if student.classroom else Period.objects.none()
    period_id = request.GET.get("periyod")
    period = periods.filter(pk=period_id).first() if period_id else periods.order_by("-order").first()
    data = _bulletin_data(student, period) if period else None
    return render(
        request,
        "grades/bulletin.html",
        {"student": student, "periods": periods, "period": period, "data": data},
    )


@login_required
def bulletin_cycle(request, student_pk):
    student = _get_student_for_view(request, student_pk)
    locked = _bulletin_locked(request, student)
    if locked:
        return locked
    periods = Period.objects.filter(school_year=student.classroom.school_year).order_by("order") if student.classroom else Period.objects.none()
    summary = []
    year_points = 0
    year_count = 0
    for p in periods:
        d = _bulletin_data(student, p)
        summary.append({"period": p, **d})
        if d["moy"] is not None:
            year_points += d["moy"]
            year_count += 1
    year_avg = round(year_points / year_count, 2) if year_count else None
    cycle_decision, tone = _decision(year_avg)
    cycle = student.classroom.level.cycle if student.classroom else None
    return render(
        request,
        "grades/bulletin_cycle.html",
        {
            "student": student,
            "cycle": cycle,
            "summary": summary,
            "year_avg": year_avg,
            "year_avg_10": round(year_avg / 2, 2) if year_avg is not None else None,
            "cycle_decision": cycle_decision,
            "tone": tone,
        },
    )


@staff_required
def grade_admin_list(request):
    grades = Grade.objects.select_related("student", "class_subject__subject", "class_subject__classroom", "period")[:500]
    return render(request, "grades/grade_list.html", {"grades": grades})


@staff_required
def bulletin_excel(request, classroom_pk):
    from core.xlsx import xlsx_response

    classroom = get_object_or_404(ClassRoom.objects.select_related("level", "school_year"), pk=classroom_pk)
    period_id = request.GET.get("periyod")
    period = Period.objects.filter(school_year=classroom.school_year, pk=period_id).first() or Period.objects.filter(
        school_year=classroom.school_year
    ).order_by("-order").first()
    subjects = list(classroom.subjects.select_related("subject").order_by("subject__name"))
    headers = ["Rang", "Matricule", "Elèvre"] + [f"{cs.subject.name} (koyef. {cs.coefficient})" for cs in subjects]
    headers += ["Mwayèn /20", "Mwayèn /10", "Desizyon"]
    rows = []
    for rank, student, avg in Grade.class_ranking(classroom, period):
        row = [rank, student.matricule, student.full_name]
        for cs in subjects:
            a = Grade.subject_average(student, cs, period)
            row.append(float(a) if a is not None else None)
        row += [avg, round(avg / 2, 2), _decision(avg)[0]]
        rows.append(row)
    name = f"bulletin_{classroom.name.replace(' ', '_')}_{period.name.replace(' ', '_') if period else ''}.xlsx"
    return xlsx_response("Bulletins", headers, rows, name)
