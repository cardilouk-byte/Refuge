from django.contrib import admin

from .models import Parent, ParentStudent, Student


class ParentStudentInline(admin.TabularInline):
    model = ParentStudent
    extra = 1
    verbose_name = "Enfant"
    verbose_name_plural = "Enfants"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("matricule", "first_name", "last_name", "classroom", "status", "user")
    list_filter = ("status", "classroom")
    search_fields = ("matricule", "first_name", "last_name", "nis", "ninu")


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "relation", "phone", "user")
    search_fields = ("first_name", "last_name", "phone")
    inlines = [ParentStudentInline]


@admin.register(ParentStudent)
class ParentStudentAdmin(admin.ModelAdmin):
    list_display = ("parent", "student", "is_primary")
    list_editable = ("is_primary",)
