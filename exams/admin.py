from django.contrib import admin

from .models import Exam


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "subject", "exam_date", "coefficient")
    list_filter = ("classroom", "subject")
