from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import teaching_staff_required
from students.models import Student

from .forms import ExamForm
from .models import Exam


def _exams_for_user(user):
    if user.is_authenticated and user.role == User.Role.ELEVE:
        student = getattr(user, "student_profile", None)
        if student and student.classroom:
            return Exam.objects.filter(classroom=student.classroom)
        return Exam.objects.none()
    if user.is_authenticated and user.role == User.Role.PARENT:
        students = Student.objects.filter(parentstudent__parent__user=user)
        return Exam.objects.filter(classroom__students__in=students).distinct()
    return Exam.objects.all()


@login_required
def exam_list(request):
    exams = _exams_for_user(request.user)
    can_manage = request.user.is_authenticated and request.user.is_teaching_staff
    return render(request, "exams/list.html", {"exams": exams, "can_manage": can_manage})


@teaching_staff_required
def exam_create(request):
    form = ExamForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Egzamen an kreye.")
        return redirect("exams:list")
    return render(request, "exams/form.html", {"form": form, "titre": "Nouvo egzamen"})


@teaching_staff_required
def exam_update(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    form = ExamForm(request.POST or None, instance=exam)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Egzamen an mete ajou.")
        return redirect("exams:list")
    return render(request, "exams/form.html", {"form": form, "titre": "Modifye egzamen"})


@teaching_staff_required
def exam_delete(request, pk):
    exam = get_object_or_404(Exam, pk=pk)
    if request.method == "POST":
        exam.delete()
        messages.success(request, "Egzamen an efase.")
        return redirect("exams:list")
    return render(request, "exams/confirm_delete.html", {"object": exam})
