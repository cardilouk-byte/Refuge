from django import forms
from django.db import models

from core.models import (
    About, Club, FAQ, GalleryImage, HeroSlide, MenuItem, NewsEvent, Program,
    Result, SchoolEvent, Service, SiteSettings, TeamMember, Testimonial,
)


def _styled(fields):
    widgets = {}
    for name in fields:
        widgets[name] = forms.TextInput(attrs={"class": "form-control"})
    return widgets


class DefaultsOptionalMixin:
    default_fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model_fields = {f.name: f for f in self._meta.model._meta.fields}
        for name in self.default_fields:
            if name in self.fields:
                self.fields[name].required = False
        for name, field in self.fields.items():
            model_field = model_fields.get(name)
            if isinstance(model_field, models.BooleanField) and model_field.default is True:
                field.initial = True

    def clean(self):
        cleaned = super().clean()
        model_fields = {f.name: f for f in self._meta.model._meta.fields}
        for name in self.default_fields:
            if name in cleaned and cleaned[name] in (None, ""):
                default = getattr(model_fields.get(name), "default", None)
                if default is not None and not callable(default):
                    cleaned[name] = default
        return cleaned


class MenuItemForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order",)
    class Meta:
        model = MenuItem
        fields = ["label", "url", "parent", "order", "is_visible"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.TextInput(attrs={"class": "form-control"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = MenuItem.objects.filter(parent__isnull=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = qs
        self.fields["parent"].empty_label = "— Meni prensipal —"


class TestimonialForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order",)
    class Meta:
        model = Testimonial
        fields = ["name", "class_name", "quote", "photo", "is_published", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "class_name": forms.TextInput(attrs={"class": "form-control"}),
            "quote": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ClubForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order",)
    class Meta:
        model = Club
        fields = ["name", "category", "description", "supervisor", "schedule", "image", "is_active", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "supervisor": forms.TextInput(attrs={"class": "form-control"}),
            "schedule": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class SchoolEventForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ()
    class Meta:
        model = SchoolEvent
        fields = ["title", "description", "location", "date", "end_date", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }


class FAQForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order",)
    class Meta:
        model = FAQ
        fields = ["question", "answer", "is_published", "order"]
        widgets = {
            "question": forms.TextInput(attrs={"class": "form-control"}),
            "answer": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class HeroSlideForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order", "button_text", "button_url")
    class Meta:
        model = HeroSlide
        fields = ["title", "subtitle", "image", "video", "button_text", "button_url", "order", "is_active"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "subtitle": forms.TextInput(attrs={"class": "form-control"}),
            "button_text": forms.TextInput(attrs={"class": "form-control"}),
            "button_url": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ServiceForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order", "icon")
    class Meta:
        model = Service
        fields = ["title", "description", "icon", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ProgramForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order", "level")
    class Meta:
        model = Program
        fields = ["name", "description", "image", "level", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class GalleryImageForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order", "category")
    class Meta:
        model = GalleryImage
        fields = ["title", "category", "image", "video", "video_url", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "video_url": forms.URLInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class NewsEventForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ()
    class Meta:
        model = NewsEvent
        fields = ["title", "image", "body", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class TeamMemberForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ("order",)
    class Meta:
        model = TeamMember
        fields = ["name", "photo", "position", "subjects", "email", "bio", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "position": forms.TextInput(attrs={"class": "form-control"}),
            "subjects": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ResultForm(DefaultsOptionalMixin, forms.ModelForm):
    default_fields = ()
    class Meta:
        model = Result
        fields = ["title", "school_year", "pdf_file", "is_public"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "school_year": forms.TextInput(attrs={"class": "form-control"}),
        }


class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        fields = [
            "title", "text", "image", "stat_students", "stat_teachers",
            "stat_years", "stat_graduates", "director_name", "director_photo",
            "director_message", "mission", "vision", "values", "history",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "director_name": forms.TextInput(attrs={"class": "form-control"}),
            "director_message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "mission": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "vision": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "values": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "history": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "stat_students": forms.NumberInput(attrs={"class": "form-control"}),
            "stat_teachers": forms.NumberInput(attrs={"class": "form-control"}),
            "stat_years": forms.NumberInput(attrs={"class": "form-control"}),
            "stat_graduates": forms.NumberInput(attrs={"class": "form-control"}),
        }


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            "name", "short_name", "logo", "motto", "address", "phone", "email",
            "facebook_url", "youtube_url", "whatsapp_url", "instagram_url",
            "google_maps_url", "copyright_text",
            "primary_color", "secondary_color", "success_color", "info_color", "warning_color", "danger_color", "header_bg_color", "header_text_color",
            "footer_bg_color", "footer_text_color", "title_font", "body_font",
            "degrade_actif", "degrade_style", "degrade_debut", "degrade_fin", "degrade_angle",
            "style_coins", "activer_animations",
            "footer_logo_1", "footer_logo_2", "footer_logo_3",
            "slider_interval", "slider_effect", "slider_autoplay",
            "section_animation", "hero_text_position", "aos_duration", "hero_overlay_opacity",
            "hero_animation",
            "marquee_enabled", "marquee_text", "marquee_speed",
            "show_hero", "show_about", "show_services", "show_programs", "show_gallery",
            "show_news", "show_team", "show_contact", "show_school_life", "show_testimonials",
            "hashtag", "inspire_texts", "admission_intro",
            "seo_title", "seo_description", "favicon",
            "site_actif", "message_maintenance",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "short_name": forms.TextInput(attrs={"class": "form-control"}),
            "motto": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "facebook_url": forms.URLInput(attrs={"class": "form-control"}),
            "youtube_url": forms.URLInput(attrs={"class": "form-control"}),
            "whatsapp_url": forms.URLInput(attrs={"class": "form-control"}),
            "instagram_url": forms.URLInput(attrs={"class": "form-control"}),
            "google_maps_url": forms.URLInput(attrs={"class": "form-control"}),
            "copyright_text": forms.TextInput(attrs={"class": "form-control"}),
            "primary_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "secondary_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "success_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "info_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "warning_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "danger_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "header_bg_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "header_text_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "footer_bg_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "footer_text_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "title_font": forms.Select(attrs={"class": "form-select"}),
            "body_font": forms.Select(attrs={"class": "form-select"}),
            "degrade_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "degrade_style": forms.Select(attrs={"class": "form-select"}),
            "degrade_debut": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "degrade_fin": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "degrade_angle": forms.NumberInput(attrs={"class": "form-control", "min": 0, "max": 360}),
            "style_coins": forms.Select(attrs={"class": "form-select"}),
            "activer_animations": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hero_animation": forms.Select(attrs={"class": "form-select"}),
            "site_actif": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "message_maintenance": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "slider_interval": forms.NumberInput(attrs={"class": "form-control"}),
            "slider_effect": forms.Select(attrs={"class": "form-select"}),
            "slider_autoplay": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "section_animation": forms.Select(attrs={"class": "form-select"}),
            "hero_text_position": forms.Select(attrs={"class": "form-select"}),
            "aos_duration": forms.NumberInput(attrs={"class": "form-control"}),
            "hero_overlay_opacity": forms.NumberInput(attrs={"class": "form-control"}),
            "marquee_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "marquee_text": forms.TextInput(attrs={"class": "form-control"}),
            "marquee_speed": forms.NumberInput(attrs={"class": "form-control"}),
            "show_hero": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_about": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_services": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_programs": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_gallery": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_news": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_team": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_contact": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_school_life": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_testimonials": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hashtag": forms.TextInput(attrs={"class": "form-control"}),
            "inspire_texts": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "admission_intro": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "seo_title": forms.TextInput(attrs={"class": "form-control"}),
            "seo_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


SETTINGS_TABS = {
    "general": ["name", "short_name", "logo", "motto", "address", "phone", "email", "copyright_text"],
    "social": ["facebook_url", "youtube_url", "whatsapp_url", "instagram_url", "google_maps_url"],
    "apparence": ["primary_color", "secondary_color", "success_color", "info_color", "warning_color", "danger_color", "header_bg_color", "header_text_color", "footer_bg_color", "footer_text_color", "title_font", "body_font", "degrade_actif", "degrade_style", "degrade_debut", "degrade_fin", "degrade_angle", "style_coins", "footer_logo_1", "footer_logo_2", "footer_logo_3"],
    "animasyon": ["activer_animations", "slider_effect", "slider_interval", "slider_autoplay", "section_animation", "aos_duration", "hero_text_position", "hero_overlay_opacity", "hero_animation", "marquee_enabled", "marquee_text", "marquee_speed"],
    "seksyon": ["show_hero", "show_about", "show_services", "show_programs", "show_gallery", "show_news", "show_team", "show_contact", "show_school_life", "show_testimonials"],
    "kontni": ["hashtag", "inspire_texts", "admission_intro"],
    "seo": ["seo_title", "seo_description", "favicon"],
    "sekirite": ["site_actif", "message_maintenance"],
}
