from django.contrib import admin

from .models import Attempt, Question, Quiz


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "class_subject", "is_published", "created_by")
    list_filter = ("is_published", "classroom")
    search_fields = ("title",)
    inlines = [QuestionInline]


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "quiz", "score", "total", "submitted_at")
    list_filter = ("quiz",)
