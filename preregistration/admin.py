from django.contrib import admin

from .models import PreRegistration


@admin.register(PreRegistration)
class PreRegistrationAdmin(admin.ModelAdmin):
    list_display = ("reference", "full_name", "status", "desired_level", "parent_name", "parent_phone", "created_at")
    list_filter = ("status", "desired_level")
    search_fields = ("reference", "first_name", "last_name", "parent_name")
    readonly_fields = ("reference", "created_at", "reviewed_by", "reviewed_at", "converted_student")
