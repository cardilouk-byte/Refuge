import calendar as pycal
from datetime import date, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils import timezone

from departments.models import Department

from .forms import ContactForm, SignUpForm
from .models import (
    About, Club, FAQ, GalleryImage, HeroSlide, MenuItem, NewsEvent, Program,
    Result, SchoolEvent, Service, SiteSettings, TeamMember, Testimonial,
)

MONTH_LABELS = {
    1: "Janvye", 2: "Fevriye", 3: "Mas", 4: "Avril", 5: "Me", 6: "Jen",
    7: "Jiy\u00e8", 8: "Out", 9: "Septanm", 10: "Okt\u00f2b", 11: "Novanm", 12: "Desanm",
}
from accounts.models import User


def home(request):
    slides = HeroSlide.objects.filter(is_active=True)
    about = About.objects.first()
    services = Service.objects.all()
    programs = Program.objects.all()
    gallery = GalleryImage.objects.all()[:12]
    news = NewsEvent.objects.filter(is_published=True)[:3]
    team = TeamMember.objects.all()

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save()
            if settings.ADMIN_EMAIL_NOTIFICATION:
                send_mail(
                    f"Nouveau message de contact : {msg.subject}",
                    f"De : {msg.name} <{msg.email}>\n\n{msg.message}",
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL_NOTIFICATION],
                    fail_silently=True,
                )
            messages.success(request, "Votre message a été envoyé avec succès. Merci !")
            return redirect("home")
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = ContactForm()

    context = {
        "slides": slides,
        "about": about,
        "services": services,
        "programs": programs,
        "gallery": gallery,
        "news": news,
        "team": team,
        "clubs": Club.objects.filter(is_active=True)[:3],
        "testimonials": Testimonial.objects.filter(is_published=True),
        "upcoming_events": SchoolEvent.objects.filter(
            is_published=True, date__gte=timezone.localdate()
        )[:3],
        "form": form,
    }
    return render(request, "core/home.html", context)


def results(request):
    if request.user.is_authenticated:
        results_qs = Result.objects.all()
    else:
        results_qs = Result.objects.filter(is_public=True)
    return render(request, "core/results.html", {"results": results_qs})


def signup(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.PARENT
            user.save()
            login(request, user)
            messages.success(request, "Bienvenue ! Votre compte a été créé avec succès.")
            return redirect("home")
        messages.error(request, "Veuillez corriger les erreurs du formulaire.")
    else:
        form = SignUpForm()

    return render(request, "core/signup.html", {"form": form})
def _month_bounds(year, month):
    prev_first = date(year, month, 1) - timedelta(days=1)
    next_month, next_year = (month + 1, year) if month < 12 else (1, year + 1)
    return prev_first, next_month, next_year


def calendar_view(request):
    today = timezone.localdate()
    try:
        year, month = (int(x) for x in request.GET.get("m", "").split("-"))
        date(year, month, 1)
    except (ValueError, TypeError):
        year, month = today.year, today.month
    first_day = date(year, month, 1)
    last_day = date(year, month, pycal.monthrange(year, month)[1])
    by_day = {}
    events = SchoolEvent.objects.filter(is_published=True, date__lte=last_day)
    for ev in events:
        if ev.end_date and ev.end_date >= first_day:
            span_start = max(ev.date, first_day)
            span_end = min(ev.end_date, last_day)
            days = range(span_start.day, span_end.day + 1)
        elif first_day <= ev.date <= last_day:
            days = [ev.date.day]
        else:
            continue
        for d in days:
            by_day.setdefault(d, []).append(ev)
    prev_first, next_month, next_year = _month_bounds(year, month)
    weeks = [
        [{"day": d, "events": by_day.get(d, [])} for d in week]
        for week in pycal.Calendar().monthdayscalendar(year, month)
    ]
    context = {
        "weeks": weeks,
        "by_day": by_day,
        "month_label": "{} {}".format(MONTH_LABELS.get(month), year),
        "prev_key": "{}-{:02d}".format(prev_first.year, prev_first.month),
        "next_key": "{}-{:02d}".format(next_year, next_month),
        "today": today,
        "upcoming": SchoolEvent.objects.filter(is_published=True, date__gte=today)[:6],
    }
    return render(request, "core/calendar.html", context)


def school_life(request):
    today = timezone.localdate()
    clubs = list(Club.objects.filter(is_active=True))
    grouped = []
    for key, label in Club.CATEGORIES:
        items = [c for c in clubs if c.category == key]
        if items:
            grouped.append({"label": label, "items": items})
    return render(request, "core/life.html", {
        "grouped": grouped,
        "upcoming": SchoolEvent.objects.filter(is_published=True, date__gte=today)[:4],
    })


def faq_page(request):
    return render(request, "core/faq.html", {
        "faqs": FAQ.objects.filter(is_published=True),
    })


HOW_TO_APPLY_STEPS = [
    ("1", "Enf\u00f2masyon el\u00e8v la", "Non, seks, dat ak kote nesans, adr\u00e8s ak yon foto (opsyon\u00e8l)."),
    ("2", "Paran / responsab", "Non paran oswa responsab a, relasyon an ak el\u00e8v la, telefon ak imel."),
    ("3", "Klas & dokiman", "Nivo w vle a, ansyen lek\u00f2l, ake nesans ak denye bilten (opsyon\u00e8l)."),
    ("4", "Rezime & soum\u00e8t", "Verifye tout enf\u00f2masyon yo, soum\u00e8t demann lan ak resevwa yon nimewo referans."),
]


def how_to_apply(request):
    settings_obj = SiteSettings.load()
    return render(request, "core/apply.html", {
        "steps": HOW_TO_APPLY_STEPS,
        "admission_intro": settings_obj.admission_intro,
        "hashtag": settings_obj.hashtag,
    })


def about_page(request):
    departments = Department.objects.filter(parent__isnull=True, is_active=True).prefetch_related("positions", "children__positions")
    return render(request, "core/about.html", {
        "about": About.objects.first(),
        "departments": departments,
    })
