from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.views import superadmin_required
from core.models import (
    About, GalleryImage, HeroSlide, MenuItem, NewsEvent, Program, Result,
    Service, SiteSettings, TeamMember,
)

from .config_forms import (
    AboutForm, GalleryImageForm, HeroSlideForm, MenuItemForm, NewsEventForm,
    ProgramForm, ResultForm, ServiceForm, SiteSettingsForm, TeamMemberForm,
    SETTINGS_TABS,
)

SECTIONS = {
    "slides": {"model": HeroSlide, "form": HeroSlideForm, "label": "Slides Hero", "icon": "bi-images", "desc": "Banner gwo paj dakèy la"},
    "meni": {"model": MenuItem, "form": MenuItemForm, "label": "Meni Navigasyon", "icon": "bi-list-ul", "desc": "Eleman meni header a"},
    "apropos": {"model": About, "form": AboutForm, "label": "À Propos", "icon": "bi-info-circle", "desc": "Prezantasyon, estatistik, direktè", "single": True},
    "sevis": {"model": Service, "form": ServiceForm, "label": "Sèvis", "icon": "bi-grid", "desc": "Kat sèvis lekòl la"},
    "pwogram": {"model": Program, "form": ProgramForm, "label": "Pwogram", "icon": "bi-journal-bookmark", "desc": "Pwogram akademik yo"},
    "galri": {"model": GalleryImage, "form": GalleryImageForm, "label": "Galri", "icon": "bi-camera", "desc": "Foto ak videyo"},
    "nouveles": {"model": NewsEvent, "form": NewsEventForm, "label": "Nouvèl / Evènman", "icon": "bi-megaphone", "desc": "Aktualite lekòl la"},
    "ekip": {"model": TeamMember, "form": TeamMemberForm, "label": "Ekip / Pwofesè", "icon": "bi-people", "desc": "Manm ekip pedagojik la"},
    "rezilta": {"model": Result, "form": ResultForm, "label": "Rezilta", "icon": "bi-file-earmark-pdf", "desc": "Fichye rezilta PDF"},
}


def _section(slug):
    return SECTIONS.get(slug)


def _single_object(cfg):
    model = cfg["model"]
    if hasattr(model, "load"):
        return model.load()
    return model.objects.first() or model.objects.create()


@superadmin_required
def config_home(request):
    return render(request, "dashboard/config/index.html", {"sections": SECTIONS})


@superadmin_required
def config_settings(request):
    settings_obj = SiteSettings.load()
    if request.method == "POST":
        form = SiteSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramèt yo anrejistre.")
            return redirect("dashboard:config_settings")
    else:
        form = SiteSettingsForm(instance=settings_obj)
    tabs_data = {name: [form[f] for f in fields] for name, fields in SETTINGS_TABS.items()}
    return render(request, "dashboard/config/settings.html", {"form": form, "tabs_data": tabs_data})


@superadmin_required
def config_list(request, section):
    cfg = _section(section)
    if cfg is None:
        messages.error(request, "Seksyon sa pa egziste.")
        return redirect("dashboard:config_home")
    if cfg.get("single"):
        return redirect("dashboard:config_update", section=section, pk=1)
    items = cfg["model"].objects.all()
    return render(request, "dashboard/config/object_list.html", {"section": section, "cfg": cfg, "items": items})


@superadmin_required
def config_create(request, section):
    cfg = _section(section)
    if cfg is None:
        messages.error(request, "Seksyon sa pa egziste.")
        return redirect("dashboard:config_home")
    if cfg.get("single"):
        return redirect("dashboard:config_update", section=section, pk=1)
    if request.method == "POST":
        form = cfg["form"](request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Eleman an kreye.")
            return redirect("dashboard:config_list", section=section)
    else:
        form = cfg["form"]()
    return render(request, "dashboard/config/object_form.html", {"section": section, "cfg": cfg, "form": form})


@superadmin_required
def config_update(request, section, pk):
    cfg = _section(section)
    if cfg is None:
        messages.error(request, "Seksyon sa pa egziste.")
        return redirect("dashboard:config_home")
    if cfg.get("single"):
        obj = _single_object(cfg)
    else:
        obj = get_object_or_404(cfg["model"], pk=pk)
    if request.method == "POST":
        form = cfg["form"](request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Chanjman yo anrejistre.")
            return redirect("dashboard:config_list", section=section)
    else:
        form = cfg["form"](instance=obj)
    return render(request, "dashboard/config/object_form.html", {"section": section, "cfg": cfg, "form": form, "obj": obj})


@superadmin_required
def config_delete(request, section, pk):
    cfg = _section(section)
    if cfg is None:
        messages.error(request, "Seksyon sa pa egziste.")
        return redirect("dashboard:config_home")
    if cfg.get("single"):
        messages.info(request, "Seksyon sa se yon sèl fich — ou pa ka efase l.")
        return redirect("dashboard:config_update", section=section, pk=1)
    obj = get_object_or_404(cfg["model"], pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, "Eleman an efase.")
        return redirect("dashboard:config_list", section=section)
    return render(request, "dashboard/config/object_confirm_delete.html", {"section": section, "cfg": cfg, "obj": obj})


@superadmin_required
def config_themes(request):
    from core.models import SiteSettings

    from .themes import SITE_THEMES

    settings_obj = SiteSettings.load()
    return render(
        request,
        "dashboard/config/themes.html",
        {"themes": SITE_THEMES, "active_theme": getattr(settings_obj, "active_theme_key", "")},
    )


@superadmin_required
def config_theme_apply(request, key):
    from django.contrib import messages

    from core.models import SiteSettings

    from .themes import get_theme

    if request.method == "POST":
        theme = get_theme(key)
        if theme:
            settings_obj = SiteSettings.load()
            settings_obj.primary_color = theme["primary"]
            settings_obj.header_bg_color = theme["header_bg"]
            settings_obj.header_text_color = theme["header_text"]
            settings_obj.footer_bg_color = theme["footer_bg"]
            settings_obj.footer_text_color = theme["footer_text"]
            settings_obj.degrade_actif = theme["degrade"]
            settings_obj.degrade_debut = theme["debut"]
            settings_obj.degrade_fin = theme["fin"]
            settings_obj.degrade_angle = theme["angle"]
            settings_obj.title_font = theme["title_font"]
            settings_obj.body_font = theme["body_font"]
            settings_obj.save()
            messages.success(request, f"Modèl « {theme['label']} » aplike!")
        return redirect("dashboard:config_themes")
    return redirect("dashboard:config_themes")
