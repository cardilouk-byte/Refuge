from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from accounts.views import staff_required, teaching_staff_required
from notifications.models import Notification

from .forms import LessonEntryForm
from .models import LessonEntry


def _my_subjects(user):
    from academics.models import ClassSubject

    qs = ClassSubject.objects.select_related("classroom", "subject").order_by(
        "classroom__school_year__label", "classroom__level__order", "subject__name"
    )
    if user.is_teaching_staff and not user.is_school_staff and not user.is_staff:
        qs = qs.filter(teacher__user=user)
    return qs


@login_required
def index(request):
    can_verify = request.user.is_school_staff or request.user.is_staff
    subjects = _my_subjects(request.user)
    subject_id = request.GET.get("matye")
    cs = subjects.filter(pk=subject_id).first() if subject_id else subjects.first()
    entries = LessonEntry.objects.none()
    if cs:
        entries = LessonEntry.objects.filter(class_subject=cs).select_related(
            "class_subject__classroom", "class_subject__subject", "created_by"
        ).order_by("-date")
    pending = LessonEntry.objects.filter(status=LessonEntry.Status.ATTENTE).count()
    return render(
        request,
        "cahiers/index.html",
        {"subjects": subjects, "cs": cs, "entries": entries, "can_verify": can_verify, "pending": pending},
    )


@teaching_staff_required
def lesson_create(request):
    form = LessonEntryForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.created_by = request.user
        entry.save()
        messages.success(request, "Cahier de tèks sove.")
        return redirect(f"/cahiers/?matye={entry.class_subject_id}")
    return render(request, "cahiers/form.html", {"form": form, "titre": "Nouvo antre cahier"})


@teaching_staff_required
def lesson_update(request, pk):
    entry = get_object_or_404(LessonEntry, pk=pk)
    if not (request.user.is_staff or request.user.is_school_staff):
        if entry.created_by_id != request.user.pk:
            raise PermissionDenied
    form = LessonEntryForm(request.POST or None, instance=entry, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Cahier de tèks mete ajou.")
        return redirect(f"/cahiers/?matye={entry.class_subject_id}")
    return render(request, "cahiers/form.html", {"form": form, "titre": "Modifye antre"})


@login_required
def lesson_delete(request, pk):
    entry = get_object_or_404(LessonEntry, pk=pk)
    allowed = request.user.is_staff or request.user.is_school_staff or entry.created_by_id == request.user.pk
    if not allowed:
        raise PermissionDenied
    if request.method == "POST":
        cid = entry.class_subject_id
        entry.delete()
        messages.success(request, "Antre efase.")
        return redirect(f"/cahiers/?matye={cid}")
    return render(request, "cahiers/confirm_delete.html", {"object": entry})


@staff_required
def verification(request):
    entries = LessonEntry.objects.filter(status=LessonEntry.Status.ATTENTE).select_related(
        "class_subject__classroom", "class_subject__subject", "created_by"
    ).order_by("-date")
    return render(request, "cahiers/verification.html", {"entries": entries})


@staff_required
def verify(request, pk):
    entry = get_object_or_404(LessonEntry, pk=pk)
    if request.method == "POST":
        action = request.POST.get("action")
        comment = request.POST.get("comment", "").strip()[:255]
        if action == "valide":
            entry.status = LessonEntry.Status.VALIDE
        elif action == "rejete":
            entry.status = LessonEntry.Status.REJETE
        else:
            return redirect("/cahiers/verifye/")
        entry.review_comment = comment
        entry.reviewed_by = request.user
        entry.save()
        if entry.created_by:
            Notification.send(
                entry.created_by,
                f"Cahier de tèks {entry.get_status_display().lower()}: {entry.class_subject} ({entry.date:%d/%m})",
                body=comment or "Verifye pa Direction.",
                url=f"/cahiers/?matye={entry.class_subject_id}",
            )
        messages.success(request, "Verification sove.")
    return redirect("/cahiers/verifye/")


@staff_required
def cahier_excel(request):
    from core.xlsx import xlsx_response

    entries = LessonEntry.objects.select_related(
        "class_subject__classroom", "class_subject__subject", "created_by", "reviewed_by"
    ).order_by("class_subject__classroom", "-date")[:2000]
    rows = [
        [
            e.class_subject.classroom.name,
            e.class_subject.subject.name,
            e.date.isoformat(),
            e.content,
            e.created_by.get_full_name() if e.created_by else "",
            e.get_status_display(),
            e.review_comment,
        ]
        for e in entries
    ]
    return xlsx_response(
        "Cahier de tèks",
        ["Klas", "Matiye", "Dat", "Sa ki fèt", "Ekri pa", "Estati", "Remak Direction"],
        rows,
        "cahier_de_teksis.xlsx",
    )
