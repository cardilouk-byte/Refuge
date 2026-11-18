from django.conf import settings
from django.contrib import admin
from django.core.mail import send_mail

from .models import (
    About, Club, ContactMessage, FAQ, GalleryImage, HeroSlide, MenuItem, NewsEvent,
    Program, Result, SchoolEvent, Service, SiteSettings, TeamMember, Testimonial,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "email", "phone")
    fieldsets = [
        ("Identité", {"fields": ["name", "short_name", "logo", "motto"]}),
        ("Contact", {"fields": ["address", "phone", "email"]}),
        ("Réseaux sociaux & Maps", {"fields": ["facebook_url", "youtube_url", "whatsapp_url", "instagram_url", "google_maps_url"]}),
        ("Apparence", {"fields": ["primary_color", "hero_overlay_opacity", "slider_interval"]}),
        ("SEO", {"fields": ["seo_title", "seo_description", "favicon"]}),
        ("Footer", {"fields": ["copyright_text"]}),
    ]

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("label", "url", "parent", "order", "is_visible")
    list_editable = ("order", "is_visible")
    list_filter = ("is_visible",)


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ("title", "order", "is_active", "image")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)


@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    list_display = ("title", "stat_students", "stat_teachers", "stat_years", "stat_graduates")

    def has_add_permission(self, request):
        return not About.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "icon", "order")
    list_editable = ("order",)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "order")
    list_editable = ("order",)
    list_filter = ("level",)


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "date", "order", "image")
    list_editable = ("order",)
    list_filter = ("category",)
    search_fields = ("title", "category")


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("title", "school_year", "published_at", "is_public")
    list_filter = ("is_public", "school_year")
    search_fields = ("title",)


@admin.register(NewsEvent)
class NewsEventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title",)


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "subjects", "order", "photo")
    list_editable = ("order",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("name", "email", "subject")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    list_editable = ("is_read",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return request.method != "POST"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change and settings.ADMIN_EMAIL_NOTIFICATION:
            send_mail(
                f"Nouveau message de contact : {obj.subject}",
                f"De : {obj.name} <{obj.email}>\n\n{obj.message}",
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL_NOTIFICATION],
                fail_silently=True,
            )


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "class_name", "order", "is_published", "photo")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "supervisor", "schedule", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("category", "is_active")


@admin.register(SchoolEvent)
class SchoolEventAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "end_date", "location", "is_published")
    list_filter = ("is_published",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order", "is_published")
    list_editable = ("order", "is_published")
    list_filter = ("is_published",)
