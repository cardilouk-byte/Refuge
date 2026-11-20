from django.contrib import admin

from .models import Grade


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("student", "class_subject", "period", "kind", "score", "created_at")
    list_filter = ("kind", "period", "class_subject__classroom")
    search_fields = ("student__first_name", "student__last_name")
