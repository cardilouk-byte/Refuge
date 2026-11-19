from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.views import teaching_staff_required
from academics.models import ClassRoom

from .forms import StudentForm, generate_password
from .models import Student

User = get_user_model()


@teaching_staff_required
def student_list(request):
    rooms = ClassRoom.objects.select_related("level", "school_year").order_by(
        "school_year__label", "level__order", "section"
    )
    room_id = request.GET.get("klas")
    q = (request.GET.get("q") or "").strip()
    students = Student.objects.select_related("classroom__level", "classroom__school_year", "user").order_by(
        "classroom__level__order", "last_name", "first_name"
    )
    if room_id:
        students = students.filter(classroom_id=room_id)
    if q:
        students = students.filter(
            Q(last_name__icontains=q) | Q(first_name__icontains=q) | Q(matricule__icontains=q)
        )
    paginator = Paginator(students, 50)
    page_obj = paginator.get_page(request.GET.get("paj"))
    return render(
        request,
        "students/student_list.html",
        {"page_obj": page_obj, "rooms": rooms, "f_classroom": room_id, "q": q},
    )


@teaching_staff_required
def student_create(request):
    form = StudentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        student = form.save(commit=False)
        try:
            student.full_clean()
        except Exception as exc:
            form.add_error(None, str(exc))
            return render(request, "students/student_form.html", {"form": form, "titre": "Nouvo elèv"})
        student.save()
        messages.success(request, f"Elèv {student.full_name} kreye ({student.matricule}).")
        return redirect("students:student_list")
    return render(request, "students/student_form.html", {"form": form, "titre": "Nouvo elèv"})


@teaching_staff_required
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, request.FILES or None, instance=student)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Elèv mete ajou.")
        return redirect("students:student_list")
    return render(request, "students/student_form.html", {"form": form, "titre": "Modifye elèv"})


@teaching_staff_required
def student_account(request, pk):
    student = get_object_or_404(Student.objects.select_related("classroom__level"), pk=pk)
    credentials = request.session.pop("student_credentials", None)
    if request.method == "POST":
        if student.user:
            user, action = student.user, "reset"
        else:
            base = student.matricule.strip().lower() or f"elv{student.pk}"
            username = base
            n = 1
            while User.objects.filter(username=username).exists():
                n += 1
                username = f"{base}{n}"
            user, action = User(username=username, role=User.Role.ELEVE), "create"
        password = generate_password()
        user.set_password(password)
        user.save()
        if action == "create":
            student.user = user
            student.save(update_fields=["user"])
        request.session["student_credentials"] = {
            "username": user.get_username(),
            "password": password,
        }
        messages.success(request, "Kont elèv la sove — fe atansyon: modpas la pa pral parèt ankò.")
        return redirect("students:student_account", student.pk)
    return render(
        request,
        "students/student_account.html",
        {"student": student, "credentials": credentials},
    )
