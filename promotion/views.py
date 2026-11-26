from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.views import staff_required
from academics.models import ClassRoom, ClassSubject, Level, SchoolYear
from notifications.models import Notification
from students.models import Student

from .forms import NewYearForm

User = get_user_model()


def _next_level(level):
    return Level.objects.filter(order__gt=level.order).order_by("order").first()


def _default_target(classroom, new_year):
    nxt = _next_level(classroom.level)
    if nxt:
        return ClassRoom.objects.filter(school_year=new_year, level=nxt, section=classroom.section).first()
    return None


def _repeat_classroom(classroom, new_year):
    return ClassRoom.objects.filter(school_year=new_year, level=classroom.level, section=classroom.section).first()


@login_required
def home(request):
    years = SchoolYear.objects.all().order_by("-label")
    return render(request, "promotion/home.html", {"years": years})


@staff_required
def new_year(request):
    form = NewYearForm(request.POST or None)
    current = SchoolYear.objects.filter(is_current=True).first()
    if request.method == "POST" and form.is_valid():
        label = form.cleaned_data["label"]
        with transaction.atomic():
            year = SchoolYear.objects.create(label=label)
            if form.cleaned_data["copy_classrooms"] and current:
                for room in current.classrooms.select_related("level").all():
                    new_room = ClassRoom.objects.filter(school_year=year, level=room.level, section=room.section).first()
                    if not new_room:
                        new_room = ClassRoom.objects.create(
                            school_year=year, level=room.level, section=room.section, main_teacher=room.main_teacher
                        )
                    for cs in room.subjects.select_related("subject").all():
                        ClassSubject.objects.get_or_create(
                            classroom=new_room, subject=cs.subject,
                            defaults={"teacher": cs.teacher, "coefficient": cs.coefficient, "weekly_hours": cs.weekly_hours},
                        )
            messages.success(request, f"Annè « {label} » kreye. Kounye a fe pasaj elèv yo klas pa klas.")
            return redirect("promotion:transition")
    return render(request, "promotion/new_year.html", {"form": form, "current": current})


def _rooms_data(old_year, new_year):
    rooms = old_year.classrooms.select_related("level", "school_year").order_by("level__order", "section")
    data = []
    for room in rooms:
        target = _default_target(room, new_year)
        repeat = _repeat_classroom(room, new_year)
        students = list(room.students.filter(status="ACTIF").order_by("last_name", "first_name"))
        data.append({"room": room, "target": target, "repeat": repeat, "students": students})
    return data


@staff_required
def transition(request):
    old_year = SchoolYear.objects.filter(pk=request.GET.get("anvye", "")).first() if request.GET.get("anvye") else None
    new_year = SchoolYear.objects.filter(pk=request.GET.get("novel", "")).first() if request.GET.get("novel") else None
    if not new_year:
        new_year = SchoolYear.objects.exclude(is_current=True).order_by("-label").first()
    if not old_year:
        old_year = SchoolYear.objects.filter(is_current=True).first() or SchoolYear.objects.order_by("-label").first()
    rooms_data = _rooms_data(old_year, new_year) if (old_year and new_year) else []
    return render(
        request,
        "promotion/transition.html",
        {
            "old_year": old_year, "new_year": new_year,
            "years": SchoolYear.objects.all().order_by("-label"),
            "rooms_data": rooms_data,
        },
    )


@staff_required
def apply(request):
    if request.method != "POST":
        return redirect("promotion:transition")
    old_year = get_object_or_404(SchoolYear, pk=request.POST.get("old_year"))
    new_year = get_object_or_404(SchoolYear, pk=request.POST.get("new_year"))

    moved = 0
    repeated = 0
    left = 0
    with transaction.atomic():
        for room in old_year.classrooms.select_related("level").all():
            target = _default_target(room, new_year)
            repeat = _repeat_classroom(room, new_year)
            for st in room.students.filter(status="ACTIF"):
                choice = request.POST.get(f"act_{st.pk}", "PASSE").upper()
                if choice == "KITE":
                    st.status = Student.Status.ARCHIVE
                    st.save(update_fields=["status"])
                    left += 1
                    continue
                if choice == "REDOUBLE" and repeat:
                    st.classroom = repeat
                    repeated += 1
                elif target:
                    st.classroom = target
                    moved += 1
                elif repeat:
                    st.classroom = repeat
                    repeated += 1
                st.save(update_fields=["classroom", "status"])
        SchoolYear.objects.exclude(pk=new_year.pk).update(is_current=False)
        new_year.is_current = True
        new_year.save()

    Notification.send_many(
        User.objects.filter(role__in=["SUPERADMIN", "DIRECTION"]),
        f"Annè {new_year.label} louvri",
        body=f"Pasaj fin fe: {moved} monte, {repeated} redouble, {left} kite lekòl la.",
        url="/nouvel-ane/pasaj/",
    )
    messages.success(request, f"Pasaj fin fe pou {new_year.label}: {moved} monte, {repeated} redouble, {left} kite lekòl la.")
    return redirect("promotion:transition")


@staff_required
def detail(request, classroom_pk):
    room = get_object_or_404(
        ClassRoom.objects.select_related("level", "school_year", "level__cycle"), pk=classroom_pk
    )
    new_year = None
    if request.GET.get("novel"):
        new_year = SchoolYear.objects.filter(pk=request.GET["novel"]).first()
    if not new_year:
        new_year = SchoolYear.objects.exclude(is_current=True).order_by("-label").first()
    entry = None
    if new_year:
        entry = next((d for d in _rooms_data(room.school_year, new_year) if d["room"].pk == room.pk), None)
    return render(
        request,
        "promotion/detail.html",
        {"room": room, "entry": entry, "new_year": new_year},
    )
