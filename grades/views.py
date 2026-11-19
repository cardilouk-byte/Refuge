from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import staff_required, teaching_staff_required
from academics.models import ClassRoom, Period
from students.models import Student

from .models import Grade

User = get_user_model()


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
    return {"rows": rows, "moy": moy, "rank": rank, "out_of": out_of, "decision": decision, "tone": tone}


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
        ranked.append({"rank": r, "student": s, "avg": a, "decision": dec, "tone": tone})
    return render(
        request,
        "grades/bulletin_class.html",
        {"classroom": classroom, "periods": periods, "period": period, "ranked": ranked},
    )


@login_required
def bulletin_student(request, student_pk):
    student = _get_student_for_view(request, student_pk)
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
            "cycle_decision": cycle_decision,
            "tone": tone,
        },
    )


@staff_required
def grade_admin_list(request):
    grades = Grade.objects.select_related("student", "class_subject__subject", "class_subject__classroom", "period")[:500]
    return render(request, "grades/grade_list.html", {"grades": grades})
