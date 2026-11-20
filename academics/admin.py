from django.contrib import admin

from .models import ClassRoom, ClassSubject, Cycle, Level, Period, ScheduleSlot, SchoolYear, Subject


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ("label", "is_current")
    list_editable = ("is_current",)


@admin.register(Cycle)
class CycleAdmin(admin.ModelAdmin):
    list_display = ("name", "order")
    list_editable = ("order",)


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("name", "cycle", "order")
    list_filter = ("cycle",)
    list_editable = ("order",)


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "school_year", "level", "section", "main_teacher")
    list_filter = ("school_year", "level")


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ("name", "school_year", "order")
    list_filter = ("school_year",)
    list_editable = ("order",)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


@admin.register(ClassSubject)
class ClassSubjectAdmin(admin.ModelAdmin):
    list_display = ("classroom", "subject", "teacher", "coefficient", "weekly_hours")
    list_filter = ("classroom", "teacher")


@admin.register(ScheduleSlot)
class ScheduleSlotAdmin(admin.ModelAdmin):
    list_display = ("class_subject", "weekday", "start_time", "end_time", "room")
    list_filter = ("weekday",)
