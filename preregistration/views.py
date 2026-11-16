from datetime import date

from django.contrib import messages
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from students.models import Parent, ParentStudent, Student

from accounts.views import role_required, staff_required

from .forms import ParentStepForm, SchoolStepForm, StudentStepForm
from .models import PreRegistration

STEP_FORMS = {1: StudentStepForm, 2: ParentStepForm, 3: SchoolStepForm}
STEP_LABELS = {1: "Elèv", 2: "Paran / Responsab", 3: "Eskolè & Dokiman", 4: "Rezime & Soumèt"}
SESSION_KEYS = {1: "pre_step1", 2: "pre_step2"}


def start(request):
    request.session.pop("pre_step1", None)
    request.session.pop("pre_step2", None)
    request.session.pop("pre_registration_pk", None)
    return redirect("preregistration:step", num=1)


def _session_data(request):
    data = {}
    data.update(request.session.get("pre_step1", {}))
    data.update(request.session.get("pre_step2", {}))
    return data


def step(request, num):
    if num not in STEP_FORMS:
        return redirect("preregistration:start")
    form_class = STEP_FORMS[num]

    if request.method == "POST":
        form = form_class(request.POST, request.FILES)
        if form.is_valid():
            if num == 3:
                pre = _create_preregistration(request, form)
                return redirect("preregistration:review")
            request.session[SESSION_KEYS[num]] = {k: str(v) for k, v in form.cleaned_data.items() if v is not None}
            return redirect("preregistration:step", num=num + 1)
    else:
        initial = _session_data(request) if num != 3 else {}
        form = form_class(initial=initial)

    return render(
        request, "preregistration/wizard.html",
        {"form": form, "step_num": num, "step_labels": STEP_LABELS},
    )


def _create_preregistration(request, school_form):
    data = _session_data(request)
    cleaned = school_form.cleaned_data
    birth_date = data.get("birth_date")
    if isinstance(birth_date, str):
        birth_date = date.fromisoformat(birth_date)
    pre = PreRegistration.objects.create(
        status="BROUILLON",
        first_name=data.get("first_name", ""),
        last_name=data.get("last_name", ""),
        gender=data.get("gender", "M"),
        birth_date=birth_date,
        birth_place=data.get("birth_place", ""),
        address=data.get("address", ""),
        photo=request.FILES.get("photo"),
        parent_name=data.get("parent_name", ""),
        parent_relation=data.get("parent_relation", "TUTEUR"),
        parent_phone=data.get("parent_phone", ""),
        parent_email=data.get("parent_email", ""),
        parent_profession=data.get("parent_profession", ""),
        desired_level=cleaned.get("desired_level"),
        previous_school=cleaned.get("previous_school", ""),
        last_class=cleaned.get("last_class", ""),
        birth_certificate=cleaned.get("birth_certificate"),
        report_card=cleaned.get("report_card"),
        notes=cleaned.get("notes", ""),
    )
    request.session.pop("pre_step1", None)
    request.session.pop("pre_step2", None)
    request.session["pre_registration_pk"] = pre.pk
    return pre


def review(request):
    pk = request.session.get("pre_registration_pk")
    if not pk:
        return redirect("preregistration:start")
    pre = get_object_or_404(PreRegistration, pk=pk)
    if request.method == "POST":
        pre.status = "SOUMET"
        pre.save()
        request.session.pop("pre_registration_pk", None)
        return render(request, "preregistration/confirmation.html", {"pre": pre})
    return render(request, "preregistration/review.html", {"pre": pre, "step_labels": STEP_LABELS})


@staff_required
def admin_list(request):
    status = request.GET.get("statut", "")
    items = PreRegistration.objects.select_related("desired_level", "converted_student")
    if status:
        items = items.filter(status=status)
    return render(
        request, "preregistration/admin_list.html",
        {"items": items, "status": status, "statuses": PreRegistration.STEPS},
    )


@staff_required
def admin_detail(request, pk):
    pre = get_object_or_404(PreRegistration, pk=pk)
    return render(request, "preregistration/admin_detail.html", {"pre": pre})


@role_required("SUPERADMIN", "DIRECTION")
def set_status(request, pk):
    pre = get_object_or_404(PreRegistration, pk=pk)
    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in ("EGZAMEN", "ACCEPTE", "REFUSE"):
            pre.status = new_status
            pre.reviewed_by = request.user
            pre.save(update_fields=["status", "reviewed_by"])
            messages.success(request, f"Preenskripsyon {pre.reference} → {pre.get_status_display()}.")
    return redirect("preregistration:admin_detail", pk=pk)


@role_required("SUPERADMIN", "DIRECTION")
def convert(request, pk):
    pre = get_object_or_404(PreRegistration, pk=pk)
    if request.method == "POST":
        if pre.converted_student:
            messages.info(request, "Preenskripsyon sa a deja konvèti.")
            return redirect("preregistration:admin_detail", pk=pk)
        parent_parts = pre.parent_name.strip().split(" ", 1)
        parent_first = parent_parts[0]
        parent_last = parent_parts[1] if len(parent_parts) > 1 else parent_parts[0]
        parent = Parent.objects.create(
            first_name=parent_first, last_name=parent_last,
            relation=pre.parent_relation, phone=pre.parent_phone, email=pre.parent_email,
        )
        student = Student.objects.create(
            matricule=_next_matricule(),
            first_name=pre.first_name, last_name=pre.last_name,
            birth_date=pre.birth_date, gender=pre.gender,
            photo=pre.photo, address=pre.address,
        )
        ParentStudent.objects.create(parent=parent, student=student, is_primary=True)
        pre.status = "INSCRIT"
        pre.converted_student = student
        pre.reviewed_by = request.user
        pre.save()
        messages.success(request, f"Elèv {student} kreye ak matricule {student.matricule}.")
    return redirect("preregistration:admin_detail", pk=pk)


def _next_matricule():
    number = Student.objects.count() + 1
    while True:
        candidate = f"ELV-{number:05d}"
        if not Student.objects.filter(matricule=candidate).exists():
            return candidate
        number += 1
