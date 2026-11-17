from django.contrib import admin

from .models import Devoir


@admin.register(Devoir)
class DevoirAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "subject", "due_date", "teacher")
    list_filter = ("classroom", "subject")
