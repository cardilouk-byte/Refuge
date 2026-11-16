from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render

from django.conf import settings

from .forms import ContactForm
from .models import (
    About, GalleryImage, HeroSlide, MenuItem, NewsEvent, Program, Result,
    Service, TeamMember,
)


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
        "form": form,
    }
    return render(request, "core/home.html", context)


def results(request):
    if request.user.is_authenticated:
        results_qs = Result.objects.all()
    else:
        results_qs = Result.objects.filter(is_public=True)
    return render(request, "core/results.html", {"results": results_qs})
