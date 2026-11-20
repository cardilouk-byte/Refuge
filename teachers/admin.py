from django.contrib import admin

from .models import Teacher


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("matricule", "first_name", "last_name", "specialty", "phone", "user")
    search_fields = ("matricule", "first_name", "last_name")
