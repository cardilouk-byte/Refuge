from django import forms

from core.models import (
    About, GalleryImage, HeroSlide, MenuItem, NewsEvent, Program, Result,
    Service, SiteSettings, TeamMember,
)


def _styled(fields):
    widgets = {}
    for name in fields:
        widgets[name] = forms.TextInput(attrs={"class": "form-control"})
    return widgets


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["label", "url", "order", "is_visible"]
        widgets = {
            "label": forms.TextInput(attrs={"class": "form-control"}),
            "url": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class HeroSlideForm(forms.ModelForm):
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


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["title", "description", "icon", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "icon": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = ["name", "description", "image", "level", "order"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["title", "category", "image", "video", "video_url", "order"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "video_url": forms.URLInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }


class NewsEventForm(forms.ModelForm):
    class Meta:
        model = NewsEvent
        fields = ["title", "image", "body", "is_published"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }


class TeamMemberForm(forms.ModelForm):
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


class ResultForm(forms.ModelForm):
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
            "director_message", "mission", "vision", "values",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "text": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "director_name": forms.TextInput(attrs={"class": "form-control"}),
            "director_message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "mission": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "vision": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "values": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
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
            "primary_color", "header_bg_color", "header_text_color",
            "footer_bg_color", "footer_text_color", "title_font", "body_font",
            "slider_interval", "slider_effect", "slider_autoplay",
            "section_animation", "hero_text_position", "aos_duration", "hero_overlay_opacity",
            "marquee_enabled", "marquee_text", "marquee_speed",
            "show_hero", "show_about", "show_services", "show_programs", "show_gallery",
            "show_news", "show_team", "show_contact",
            "seo_title", "seo_description", "favicon",
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
            "header_bg_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "header_text_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "footer_bg_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "footer_text_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
            "title_font": forms.Select(attrs={"class": "form-select"}),
            "body_font": forms.Select(attrs={"class": "form-select"}),
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
            "seo_title": forms.TextInput(attrs={"class": "form-control"}),
            "seo_description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


SETTINGS_TABS = {
    "general": ["name", "short_name", "logo", "motto", "address", "phone", "email", "copyright_text"],
    "social": ["facebook_url", "youtube_url", "whatsapp_url", "instagram_url", "google_maps_url"],
    "apparence": ["primary_color", "header_bg_color", "header_text_color", "footer_bg_color", "footer_text_color", "title_font", "body_font"],
    "animasyon": ["slider_effect", "slider_interval", "slider_autoplay", "section_animation", "aos_duration", "hero_text_position", "hero_overlay_opacity", "marquee_enabled", "marquee_text", "marquee_speed"],
    "seksyon": ["show_hero", "show_about", "show_services", "show_programs", "show_gallery", "show_news", "show_team", "show_contact"],
    "seo": ["seo_title", "seo_description", "favicon"],
}
