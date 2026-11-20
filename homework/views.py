from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import teaching_staff_required
from students.models import Student

from .forms import DevoirForm
from .models import Devoir


def _devoirs_for_user(user):
    if user.is_authenticated and user.role == User.Role.ELEVE:
        student = getattr(user, "student_profile", None)
        if student and student.classroom:
            return Devoir.objects.filter(classroom=student.classroom)
        return Devoir.objects.none()
    if user.is_authenticated and user.role == User.Role.PARENT:
        students = Student.objects.filter(parentstudent__parent__user=user)
        return Devoir.objects.filter(classroom__students__in=students).distinct()
    return Devoir.objects.all()


@login_required
def devoir_list(request):
    devoirs = _devoirs_for_user(request.user)
    can_manage = request.user.is_authenticated and request.user.is_teaching_staff
    return render(request, "homework/list.html", {"devoirs": devoirs, "can_manage": can_manage})


@teaching_staff_required
def devoir_create(request):
    form = DevoirForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        devoir = form.save(commit=False)
        devoir.created_by = request.user
        devoir.save()
        messages.success(request, "Devoir la kreye.")
        return redirect("homework:list")
    return render(request, "homework/form.html", {"form": form, "titre": "Nouvo devoir"})


@teaching_staff_required
def devoir_update(request, pk):
    devoir = get_object_or_404(Devoir, pk=pk)
    form = DevoirForm(request.POST or None, request.FILES or None, instance=devoir)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Devoir la mete ajou.")
        return redirect("homework:list")
    return render(request, "homework/form.html", {"form": form, "titre": "Modifye devoir"})


@teaching_staff_required
def devoir_delete(request, pk):
    devoir = get_object_or_404(Devoir, pk=pk)
    if request.method == "POST":
        devoir.delete()
        messages.success(request, "Devoir la efase.")
        return redirect("homework:list")
    return render(request, "homework/confirm_delete.html", {"object": devoir})
