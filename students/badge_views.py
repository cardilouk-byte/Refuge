import io

import qrcode
import qrcode.image.svg
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from accounts.models import User
from accounts.views import teaching_staff_required
from students.models import Student


def _qr_svg(url):
    factory = qrcode.image.svg.SvgPathImage
    img = qrcode.make(url, image_factory=factory, box_size=10, border=2)
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue().decode()


@login_required
def badge_own(request):
    student = getattr(request.user, "student_profile", None)
    if student is None:
        raise Http404
    return _render_badge(request, student)


@teaching_staff_required
def badge_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return _render_badge(request, student)


def badge_verify(request, matricule):
    student = Student.objects.filter(matricule=matricule, status=Student.Status.ACTIF).first()
    return render(request, "students/badge_verify.html", {"student": student, "matricule": matricule})


def _render_badge(request, student):
    verify_url = request.build_absolute_uri(reverse("students:badge_verify", args=[student.matricule]))
    qr_svg = _qr_svg(verify_url)
    return render(request, "students/badge.html", {"student": student, "qr_svg": qr_svg, "verify_url": verify_url})
