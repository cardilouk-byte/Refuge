from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import User
from accounts.views import staff_required, teaching_staff_required
from academics.models import ClassRoom
from students.models import Student

from .models import AttendanceRecord

User = get_user_model()


def _my_students(user):
    if user.is_authenticated and user.role == User.Role.ELEVE:
        st = getattr(user, "student_profile", None)
        return Student.objects.filter(pk=st.pk) if st else Student.objects.none()
    if user.is_authenticated and user.role == User.Role.PARENT:
        return Student.objects.filter(parentstudent__parent__user=user)
    return Student.objects.none()


@login_required
def home(request):
    if request.user.is_teaching_staff or request.user.is_staff:
        classrooms = ClassRoom.objects.select_related("level", "school_year").order_by(
            "school_year__label", "level__order", "section"
        )
        for c in classrooms:
            c.nb_students = c.students.filter(status="ACTIF").count()
        return render(request, "attendance/class_list.html", {"classrooms": classrooms})
    students = _my_students(request.user)
    records = AttendanceRecord.objects.filter(student__in=students).select_related("student").order_by("-date")[:200]
    return render(request, "attendance/records.html", {"records": records, "students": students})


@teaching_staff_required
def take(request, classroom_pk):
    classroom = get_object_or_404(ClassRoom.objects.select_related("level", "school_year"), pk=classroom_pk)
    raw_date = request.GET.get("dat") or request.POST.get("dat")
    try:
        day = timezone.datetime.fromisoformat(raw_date).date() if raw_date else timezone.localdate()
    except ValueError:
        day = timezone.localdate()

    students = list(classroom.students.filter(status="ACTIF").order_by("last_name", "first_name"))
    existing = {r.student_id: r for r in AttendanceRecord.objects.filter(student__in=students, date=day)}
    statuses = AttendanceRecord.Status.choices

    if request.method == "POST":
        saved = 0
        for st in students:
            status = request.POST.get(f"status_{st.pk}", "").strip()
            if status not in AttendanceRecord.Status.values:
                continue
            justified = request.POST.get(f"justifie_{st.pk}") == "on"
            note = request.POST.get(f"note_{st.pk}", "").strip()[:255]
            AttendanceRecord.objects.update_or_create(
                student=st,
                date=day,
                defaults={
                    "status": status,
                    "justified": justified,
                    "note": note,
                    "recorded_by": request.user,
                },
            )
            saved += 1
        messages.success(request, f"Presans sove pou {saved} elèv — {day:%d/%m/%Y}.")
        return redirect(f"{request.path}?dat={day.isoformat()}")

    return render(
        request,
        "attendance/take.html",
        {
            "classroom": classroom,
            "day": day,
            "students": students,
            "existing": existing,
            "statuses": statuses,
            "today": timezone.localdate(),
        },
    )


@staff_required
def report(request):
    classrooms = ClassRoom.objects.select_related("level", "school_year").order_by("school_year__label", "level__order", "section")
    students = Student.objects.filter(status="ACTIF").order_by("last_name", "first_name")

    classroom_id = request.GET.get("klas")
    student_id = request.GET.get("eleve")
    start = request.GET.get("debut")
    end = request.GET.get("fin")

    qs = AttendanceRecord.objects.select_related("student")
    if classroom_id:
        qs = qs.filter(student__classroom_id=classroom_id)
    if student_id:
        qs = qs.filter(student_id=student_id)
    try:
        if start:
            qs = qs.filter(date__gte=timezone.datetime.fromisoformat(start).date())
        if end:
            qs = qs.filter(date__lte=timezone.datetime.fromisoformat(end).date())
    except ValueError:
        pass

    stats = qs.values("student__pk", "student__first_name", "student__last_name", "student__matricule").annotate(
        absans=Count("id", filter=Q(status="ABSENT")),
        retad=Count("id", filter=Q(status="RETARD")),
        prezan=Count("id", filter=Q(status="PRESENT")),
    ).order_by("-absans", "-retad", "student__last_name")

    recent = qs.order_by("-date")[:200]

    return render(
        request,
        "attendance/report.html",
        {
            "classrooms": classrooms,
            "students": students,
            "stats": stats,
            "recent": recent,
            "f_classroom": classroom_id or "",
            "f_student": student_id or "",
            "f_start": start or "",
            "f_end": end or "",
        },
    )


@staff_required
def report_excel(request):
    from core.xlsx import xlsx_response

    classroom_id = request.GET.get("klas")
    student_id = request.GET.get("eleve")
    start = request.GET.get("debut")
    end = request.GET.get("fin")
    qs = AttendanceRecord.objects.select_related("student")
    if classroom_id:
        qs = qs.filter(student__classroom_id=classroom_id)
    if student_id:
        qs = qs.filter(student_id=student_id)
    try:
        if start:
            qs = qs.filter(date__gte=timezone.datetime.fromisoformat(start).date())
        if end:
            qs = qs.filter(date__lte=timezone.datetime.fromisoformat(end).date())
    except ValueError:
        pass
    stats = qs.values("student__matricule", "student__first_name", "student__last_name").annotate(
        absans=Count("id", filter=Q(status="ABSENT")),
        retad=Count("id", filter=Q(status="RETARD")),
        prezan=Count("id", filter=Q(status="PRESENT")),
    ).order_by("-absans", "-retad")
    rows = [
        [s["student__matricule"], f'{s["student__first_name"]} {s["student__last_name"]}', s["absans"], s["retad"], s["prezan"]]
        for s in stats
    ]
    return xlsx_response("Presans", ["Matricule", "Elèv", "Absans", "Retad", "Prezan"], rows, "rapor_presans.xlsx")
