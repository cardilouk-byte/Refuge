from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from academics.models import Period, ScheduleSlot, SchoolYear
from attendance.models import AttendanceRecord
from grades.models import Grade
from students.models import Student

from accounts.views import role_required


def _current_year():
    return SchoolYear.objects.filter(is_current=True).first() or SchoolYear.objects.first()


@login_required
@role_required("ENSEIGNANT")
def professeur(request):
    teacher = getattr(request.user, "teacher_profile", None)
    assignments = []
    slots = []
    if teacher:
        assignments = teacher.assignments.select_related("classroom", "subject")
        slots = ScheduleSlot.objects.filter(class_subject__teacher=teacher).select_related(
            "class_subject__classroom", "class_subject__subject"
        )
    recent_grades = Grade.objects.filter(entered_by=request.user).select_related(
        "student", "class_subject__subject"
    )[:10]
    return render(request, "portals/professeur.html", {
        "teacher": teacher,
        "assignments": assignments,
        "slots": slots,
        "recent_grades": recent_grades,
    })


@login_required
@role_required("ELEVE")
def eleve(request):
    student = getattr(request.user, "student_profile", None)
    if student is None:
        return render(request, "portals/no_profile.html", {
            "message": "Aucun dossier élève n'est lié à votre compte. Contactez l'administration."
        })

    year = _current_year()
    periods = Period.objects.filter(school_year=year) if year else Period.objects.none()
    selected_period = None
    period_id = request.GET.get("periode")
    if period_id:
        try:
            selected_period = periods.get(pk=period_id)
        except (Period.DoesNotExist, ValueError):
            selected_period = None
    if selected_period is None:
        selected_period = periods.order_by("order").last()

    subject_rows = []
    general_average = None
    if student.classroom and selected_period:
        for cs in student.classroom.subjects.select_related("subject"):
            avg = Grade.subject_average(student, cs, selected_period)
            subject_rows.append({"class_subject": cs, "average": avg})
        general_average = Grade.general_average(student, selected_period)

    attendance = student.attendance_records.all()[:30]
    attendance_counts = {
        "PRESENT": student.attendance_records.filter(status="PRESENT").count(),
        "ABSENT": student.attendance_records.filter(status="ABSENT").count(),
        "RETARD": student.attendance_records.filter(status="RETARD").count(),
    }
    slots = ScheduleSlot.objects.filter(class_subject__classroom=student.classroom).select_related(
        "class_subject__subject"
    ) if student.classroom else ScheduleSlot.objects.none()
    invoices = student.invoices.all()

    return render(request, "portals/eleve.html", {
        "student": student,
        "periods": periods,
        "selected_period": selected_period,
        "subject_rows": subject_rows,
        "general_average": general_average,
        "attendance": attendance,
        "attendance_counts": attendance_counts,
        "slots": slots,
        "invoices": invoices,
    })


@login_required
@role_required("PARENT")
def parent_home(request):
    parent = getattr(request.user, "parent_profile", None)
    children = parent.students.select_related("classroom").all() if parent else []
    return render(request, "portals/parent.html", {
        "parent": parent,
        "children": children,
    })


@login_required
@role_required("PARENT")
def child_detail(request, pk):
    parent = getattr(request.user, "parent_profile", None)
    student = None
    if parent:
        try:
            student = parent.students.select_related("classroom").get(pk=pk)
        except Student.DoesNotExist:
            student = None
    if student is None:
        return redirect("portals:parent")

    year = _current_year()
    periods = Period.objects.filter(school_year=year) if year else Period.objects.none()
    averages = []
    for period in periods:
        averages.append({
            "period": period,
            "average": Grade.general_average(student, period),
        })
    attendance_counts = {
        "PRESENT": student.attendance_records.filter(status="PRESENT").count(),
        "ABSENT": student.attendance_records.filter(status="ABSENT").count(),
        "RETARD": student.attendance_records.filter(status="RETARD").count(),
    }
    return render(request, "portals/child_detail.html", {
        "student": student,
        "averages": averages,
        "attendance_counts": attendance_counts,
        "invoices": student.invoices.all(),
    })
