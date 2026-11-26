import io
import re
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from reportlab.lib.colors import Color

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
    from .carnet import is_official_level
    return is_official_level(level_name)


@login_required
def carnet_print(request, student_pk):
    """Aper\u00e7u livret A5 nan navigatè a — 2 mòd: lekti (frape paj) / livret (2 paj A5 sou A4)."""
    student = _get_student_for_view(request, student_pk)
    locked = _carnet_locked(request, student)
    if locked:
        return locked
    from .carnet import build_carnet
    context = build_carnet(student)
    from .carnet import build_html_pages, html_sides
    pages = build_html_pages(context)
    mod = request.GET.get("mod", "lekti")
    if mod not in ("lekti", "livret"):
        mod = "lekti"
    sides = html_sides(pages) if mod == "livret" else None
    return render(
        request,
        "grades/carnet_print.html",
        {
            "carnet": CarnetSettings.load(),
            **context,
            "pages": pages,
            "sides": sides,
            "mod": mod,
            "show_graph": CarnetSettings.load().show_graph,
            "id_rows": carnet_id_rows(student),
            "titre": "Karn\u00e8 \u2014 " + student.full_name,
        },
    )


def _carnet_locked(request, student):
    """Karnè a bloke pou elèv/paran si fakti a poko peye (menm patwòn ke bulletin)."""
    if request.user.is_staff or request.user.role in (User.Role.SUPERADMIN, User.Role.DIRECTION, User.Role.ENSEIGNANT):
        return None
    if request.user.role not in (User.Role.ELEVE, User.Role.PARENT):
        return None
    is_guardian = (
        getattr(request.user, "student_profile", None) is not None
        or Student.objects.filter(parentstudent__parent__user=request.user).exists()
    )
    if not is_guardian:
        return None
    unpaid = Invoice.objects.filter(student=student).exclude(status=Invoice.Status.PAYE).exists()
    if unpaid:
        return render(request, "grades/carnet_locked.html", {"student": student})
    return None


def carnet_id_rows(student):
    classroom = student.classroom
    return [
        ("Nom", student.last_name),
        ("Pr\u00e9nom", student.first_name),
        ("Date de naissance", student.birth_date.strftime("%d/%m/%Y") if student.birth_date else "\u2014"),
        ("Sexe", {"M": "Masculin", "F": "F\u00e9minin"}.get(student.gender, "\u2014")),
        ("Classe", classroom.name if classroom else "\u2014"),
        ("Niveau", classroom.level.name if classroom else "\u2014"),
        ("Ann\u00e9e Scolaire", classroom.school_year.label if classroom else "\u2014"),
    ]


@login_required
def carnet_pdf(request, student_pk):
    student = _get_student_for_view(request, student_pk)
    locked = _carnet_locked(request, student)
    if locked:
        return locked
    from .carnet import build_carnet
    from .pdf import CarnetRenderer
    from core.models import SiteSettings

    mod = request.GET.get("mod", "lekti")
    if mod not in ("lekti", "livret"):
        mod = "lekti"
    data = build_carnet(student)
    renderer = CarnetRenderer(data, CarnetSettings.load(), SiteSettings.load())
    pdf_bytes = renderer.render(mod=mod)
    suffix = "livret" if mod == "livret" else "lekti"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="carnet_{student.matricule}_{suffix}.pdf"'
    return resp


@teaching_staff_required
def carnet_class_pdf(request, classroom_pk):
    """Karn\u00e8 an pis pou tout el\u00e8v yon klas (yon s\u00e8l PDF, chak el\u00e8v ap gen livret li)."""
    classroom = get_object_or_404(ClassRoom.objects.select_related("level", "school_year"), pk=classroom_pk)
    from .carnet import build_carnet
    from .pdf import CarnetRenderer
    from core.models import SiteSettings

    mod = request.GET.get("mod", "livret")
    if mod not in ("lekti", "livret"):
        mod = "livret"
    carnet = CarnetSettings.load()
    site = SiteSettings.load()
    buf = io.BytesIO()
    from reportlab.lib.pagesizes import A5, A4, landscape
    from reportlab.pdfgen import canvas as rl_canvas
    from grades.pdf import A5W, A5H, A4LW, A4LH

    c = rl_canvas.Canvas(buf, pagesize=(A4LW, A4LH) if mod == "livret" else A5)
    students = list(classroom.students.filter(status="ACTIF"))
    first = True
    for student in students:
        data = build_carnet(student)
        renderer = CarnetRenderer(data, carnet, site)
        pages = renderer.build_pages()
        if not pages:
            continue
        if mod == "livret":
            from .carnet import livret_sides
            while len(pages) % 4:
                pages.append({"kind": "blank"})
            sides = livret_sides(list(range(len(pages))))
            for side in sides:
                for half, page_no in enumerate(side):
                    if page_no is None:
                        continue
                    x0 = 0 if half == 0 else (A4LW - A5W)
                    if not first:
                        c.showPage()
                    first = False
                    c.saveState()
                    c.translate(x0, 0)
                    c.setFillColor(Color(1, 1, 1))
                    c.rect(0, 0, A5W, A5H, stroke=0, fill=1)
                    c.setStrokeColor(renderer.border)
                    c.setLineWidth(0.4)
                    c.line(A5W, 0, A5W, A5H)
                    renderer._draw_one(c, pages[page_no], A5W, A5H)
                    c.restoreState()
        else:
            for page in pages:
                if not first:
                    c.showPage()
                first = False
                c.saveState()
                c.setFillColor(Color(1, 1, 1))
                c.rect(0, 0, A5W, A5H, stroke=0, fill=1)
                renderer._draw_one(c, page, A5W, A5H)
                c.restoreState()
    if not first:
        c.showPage()
    c.save()
    pdf_bytes = buf.getvalue()
    suffix = "livret" if mod == "livret" else "lekti"
    name = f"carnet_{classroom.level.name.replace(' ', '_')}{classroom.section}_{suffix}.pdf"
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{name}"'
    return resp


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
