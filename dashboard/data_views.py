from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.views import direction_required
from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from teachers.models import Teacher

from .data_forms import (
    ClassRoomForm,
    ClassSubjectForm,
    CycleForm,
    LevelForm,
    PeriodForm,
    SchoolYearForm,
    SubjectForm,
    TeacherForm,
    _generate_teacher_password,
)


class DataKey:
    def __init__(self, key, titre, icon, model, form, columns, queryset=None, search=None):
        self.key = key
        self.titre = titre
        self.icon = icon
        self.model = model
        self.form = form
        self.columns = columns
        self._queryset = queryset
        self.search = search or []

    def queryset(self):
        return self._queryset() if self._queryset else self.model.objects.all()

    def display(self, obj, col):
        field, kind = col[1], col[2]
        value = getattr(obj, field, None)
        if kind == "bool":
            return ("Wi", "text-bg-success") if value else ("Non", "text-bg-secondary")
        return (str(value) if value else "\u2014", None)


DATA_MODELS = {
    "ane": DataKey(
        "ane", "Ane skol\u00e8 yo", "bi-calendar3", SchoolYear, SchoolYearForm,
        [("Lib\u00e8l", "label", "text"), ("Nan kour", "is_current", "bool")],
        search=["label"],
    ),
    "sik": DataKey(
        "sik", "Sik yo", "bi-diagram-3-fill", Cycle, CycleForm,
        [("Non", "name", "text"), ("L\u00f2d", "order", "text")],
        search=["name"],
    ),
    "nivo": DataKey(
        "nivo", "Nivo yo", "bi-layers", Level, LevelForm,
        [("Non", "name", "text"), ("Sik", "cycle", "fk"), ("L\u00f2d", "order", "text")],
        queryset=lambda: Level.objects.select_related("cycle"),
        search=["name", "cycle__name"],
    ),
    "periyod": DataKey(
        "periyod", "Periy\u00f2d yo", "bi-hourglass-split", Period, PeriodForm,
        [("Non", "name", "text"), ("Ane", "school_year", "fk"), ("L\u00f2d", "order", "text")],
        queryset=lambda: Period.objects.select_related("school_year"),
        search=["name", "school_year__label"],
    ),
    "klas": DataKey(
        "klas", "Klas yo", "bi-door-open", ClassRoom, ClassRoomForm,
        [("Klas", "name", "text"), ("Nivo", "level", "fk"), ("Ane", "school_year", "fk"), ("Titul\u00e8", "main_teacher", "fk")],
        queryset=lambda: ClassRoom.objects.select_related("level", "school_year", "main_teacher"),
        search=["level__name", "section", "school_year__label"],
    ),
    "matiye": DataKey(
        "matiye", "Maty\u00e8 yo", "bi-collection", Subject, SubjectForm,
        [("Non", "name", "text"), ("K\u00f2d", "code", "text")],
        search=["name", "code"],
    ),
    "pwofese": DataKey(
        "pwofese", "Pwofes\u00e8 yo", "bi-person-video3", Teacher, TeacherForm,
        [("Pwofes\u00e8", "__str__", "text"), ("Matrikil", "matricule", "text"), ("Espesyalite", "specialty", "text"), ("Kont", "user", "fk")],
        queryset=lambda: Teacher.objects.select_related("user"),
        search=["first_name", "last_name", "matricule", "specialty"],
    ),
    "asiyman": DataKey(
        "asiyman", "Maty\u00e8 pa klas (profes\u00e8)", "bi-link-45deg", ClassSubject, ClassSubjectForm,
        [("Klas", "classroom", "fk"), ("Maty\u00e8", "subject", "fk"), ("Profes\u00e8", "teacher", "fk"), ("Koyefisyan", "coefficient", "text")],
        queryset=lambda: ClassSubject.objects.select_related("classroom__level", "classroom__school_year", "subject", "teacher"),
        search=["classroom__level__name", "subject__name", "teacher__first_name", "teacher__last_name"],
    ),
}


def _rows(dk, items):
    rows = []
    for obj in items:
        cells = [dk.display(obj, col)[0] for col in dk.columns]
        rows.append((obj.pk, cells))
    return rows


def _get_dk(request, key):
    dk = DATA_MODELS.get(key)
    if not dk:
        return None
    return dk


@direction_required
def data_home(request):
    cards = [
        {"key": dk.key, "titre": dk.titre, "icon": dk.icon, "count": dk.queryset().count()}
        for dk in DATA_MODELS.values()
    ]
    return render(request, "dashboard/data/home.html", {"titre": "Done lek\u00f2l la", "cards": cards})


@direction_required
def data_list(request, key):
    dk = _get_dk(request, key)
    if not dk:
        return redirect("dashboard:data_home")
    items = dk.queryset()
    q = (request.GET.get("q") or "").strip()
    if q and dk.search:
        from django.db.models import Q

        cond = Q()
        for field in dk.search:
            cond |= Q(**{f"{field}__icontains": q})
        items = items.filter(cond)
    return render(
        request,
        "dashboard/data/list.html",
        {"titre": dk.titre, "dk": dk, "key": dk.key, "headers": [c[0] for c in dk.columns], "rows": _rows(dk, items), "q": q},
    )


@direction_required
def data_create(request, key):
    dk = _get_dk(request, key)
    if not dk:
        return redirect("dashboard:data_home")
    if request.method == "POST":
        form = dk.form(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if key == "pwofese" and not obj.matricule:
                obj.matricule = _next_teacher_matricule()
            try:
                obj.full_clean()
            except Exception as exc:
                form.add_error(None, str(exc))
            else:
                obj.save()
                messages.success(request, f"{obj} sove.")
                return redirect("dashboard:data_list", key=key)
    else:
        form = dk.form()
    return render(
        request,
        "dashboard/data/form.html",
        {"titre": f"Nouvo \u2014 {dk.titre.rstrip('yo').strip()}", "form": form, "dk": dk, "key": key},
    )


@direction_required
def data_update(request, key, pk):
    dk = _get_dk(request, key)
    if not dk:
        return redirect("dashboard:data_home")
    obj = get_object_or_404(dk.model, pk=pk)
    if request.method == "POST":
        form = dk.form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.full_clean()
            except Exception as exc:
                form.add_error(None, str(exc))
            else:
                obj.save()
                messages.success(request, "Chanjman yo sove.")
                return redirect("dashboard:data_list", key=key)
    else:
        form = dk.form(instance=obj)
    return render(
        request,
        "dashboard/data/form.html",
        {"titre": f"Modifye \u2014 {obj}", "form": form, "dk": dk, "key": key},
    )


@direction_required
def data_delete(request, key, pk):
    dk = _get_dk(request, key)
    if not dk:
        return redirect("dashboard:data_home")
    obj = get_object_or_404(dk.model, pk=pk)
    if request.method == "POST":
        label = str(obj)
        try:
            obj.delete()
            messages.success(request, f"{label} efase.")
        except Exception as exc:
            messages.error(request, f"Paka efase \u2014 li s\u00e8vi nan l\u00f2t b\u00f2. ({exc})")
        return redirect("dashboard:data_list", key=key)
    return render(
        request,
        "dashboard/data/delete.html",
        {"titre": f"Konfime efase \u2014 {obj}", "obj": obj,
         "cells": [dk.display(obj, col)[0] for col in dk.columns],
         "headers": [c[0] for c in dk.columns], "key": key},
    )


def _next_teacher_matricule():
    number = Teacher.objects.count() + 1
    while True:
        candidate = f"PROF-{number:03d}"
        if not Teacher.objects.filter(matricule=candidate).exists():
            return candidate
        number += 1


@direction_required
def teacher_account(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    credentials = request.session.pop("teacher_credentials", None)
    if request.method == "POST":
        if teacher.user:
            user, action = teacher.user, "reset"
        else:
            base = teacher.matricule.strip().lower() or f"prof{teacher.pk}"
            username, n = base, 1
            while User.objects.filter(username=username).exists():
                n += 1
                username = f"{base}{n}"
            user, action = (
                User(username=username, role=User.Role.ENSEIGNANT,
                     first_name=teacher.first_name, last_name=teacher.last_name),
                "create",
            )
        password = _generate_teacher_password()
        user.set_password(password)
        user.save()
        if action == "create":
            teacher.user = user
            teacher.save(update_fields=["user"])
        request.session["teacher_credentials"] = {
            "username": user.get_username(),
            "password": password,
            "who": str(teacher),
        }
        messages.success(request, "Kont profes\u00e8 a sove \u2014 fe atansyon, modpas la pa pral par\u00e8t ank\u00f2.")
        return redirect("dashboard:teacher_account", teacher.pk)
    return render(
        request,
        "dashboard/data/teacher_account.html",
        {"titre": f"Kont profes\u00e8 a \u2014 {teacher}", "teacher": teacher, "credentials": credentials},
    )
