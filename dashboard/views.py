from django.db.models import Avg, Count, Sum
from django.shortcuts import render

from academics.models import ClassRoom, Period, SchoolYear, Subject
from attendance.models import AttendanceRecord
from finance.models import Invoice, Payment
from grades.models import Grade
from students.models import Student
from teachers.models import Teacher

from accounts.views import dashboard_required


def _current_year():
    return SchoolYear.objects.filter(is_current=True).first() or SchoolYear.objects.first()


@dashboard_required
def home(request):
    year = _current_year()
    period = Period.objects.filter(school_year=year).order_by("order").last() if year else None

    stats = {
        "students": Student.objects.filter(status="ACTIF").count(),
        "teachers": Teacher.objects.count(),
        "classrooms": ClassRoom.objects.filter(school_year=year).count() if year else ClassRoom.objects.count(),
        "subjects": Subject.objects.count(),
    }

    payments_total = Payment.objects.aggregate(total=Sum("amount"))["total"] or 0
    invoices_total = Invoice.objects.aggregate(total=Sum("amount"))["total"] or 0
    finance = {
        "payments_total": payments_total,
        "invoices_total": invoices_total,
        "balance": invoices_total - payments_total,
        "unpaid_count": Invoice.objects.exclude(status="PAYE").count(),
    }

    attendance_map = {
        row["status"]: row["n"]
        for row in AttendanceRecord.objects.values("status").annotate(n=Count("id"))
    }
    attendance_total = sum(attendance_map.values())
    attendance_rate = (
        round(attendance_map.get("PRESENT", 0) * 100 / attendance_total, 1)
        if attendance_total else None
    )

    subject_averages = []
    if period:
        subject_averages = list(
            Grade.objects.filter(period=period)
            .values("class_subject__subject__name")
            .annotate(avg=Avg("score"))
            .order_by("class_subject__subject__name")[:10]
        )

    context = {
        "year": year,
        "period": period,
        "stats": stats,
        "finance": finance,
        "attendance_rate": attendance_rate,
        "attendance_map": attendance_map,
        "recent_students": Student.objects.select_related("classroom").order_by("-enrolled_at")[:5],
        "recent_grades": Grade.objects.select_related(
            "student", "class_subject__subject", "period"
        ).order_by("-created_at")[:8],
        "chart_labels": [row["class_subject__subject__name"] for row in subject_averages],
        "chart_values": [float(row["avg"]) for row in subject_averages],
    }
    return render(request, "dashboard/dashboard.html", context)
