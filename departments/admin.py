from django.contrib import admin

from .models import Department, StaffPosition


class StaffPositionInline(admin.TabularInline):
    model = StaffPosition
    extra = 0


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "kind", "parent", "head_title", "order", "is_active")
    list_filter = ("kind", "is_active")
    search_fields = ("name", "code")
    list_editable = ("order", "is_active")
    inlines = [StaffPositionInline]


@admin.register(StaffPosition)
class StaffPositionAdmin(admin.ModelAdmin):
    list_display = ("title", "department", "person_name", "is_head", "order")
    list_filter = ("department", "is_head")
    search_fields = ("title", "external_name")
