from django.conf import settings
from django.db import models


class Quiz(models.Model):
    classroom = models.ForeignKey(
        "academics.ClassRoom", on_delete=models.CASCADE,
        related_name="quizzes", verbose_name="Klas",
    )
    class_subject = models.ForeignKey(
        "academics.ClassSubject", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="quizzes", verbose_name="Matiye",
    )
    title = models.CharField("Tit", max_length=200)
    description = models.TextField("Deskripsyon", blank=True)
    due_date = models.DateField("Dat litm (facultatif)", blank=True, null=True)
    is_published = models.BooleanField("Pibliye (voye bay elèv)", default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="quizzes_created", verbose_name="Kreye pa",
    )
    created_at = models.DateTimeField("Kreye le", auto_now_add=True)

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quizs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.classroom}"

    @property
    def total_points(self):
        return sum(q.points for q in self.questions.all())


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions", verbose_name="Quiz")
    text = models.TextField("Kesyon")
    option_a = models.CharField("Chwa A", max_length=255)
    option_b = models.CharField("Chwa B", max_length=255)
    option_c = models.CharField("Chwa C", max_length=255, blank=True)
    option_d = models.CharField("Chwa D", max_length=255, blank=True)
    correct = models.CharField("Bon repons", max_length=1, choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    points = models.PositiveIntegerField("Pwen", default=1)
    order = models.PositiveIntegerField("Orde", default=0)

    class Meta:
        verbose_name = "Kesyon quiz"
        verbose_name_plural = "Kesyon quizs"
        ordering = ["order", "pk"]

    def __str__(self):
        return f"{self.quiz.title} — {self.text[:40]}"


class Attempt(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts", verbose_name="Quiz")
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE,
        related_name="quiz_attempts", verbose_name="Elèv",
    )
    score = models.DecimalField("Pwen", max_digits=6, decimal_places=2)
    total = models.DecimalField("Total pwen", max_digits=6, decimal_places=2)
    submitted_at = models.DateTimeField("Soumise le", auto_now_add=True)

    class Meta:
        verbose_name = "Repons quiz"
        verbose_name_plural = "Repons quizs"
        ordering = ["score"]
        unique_together = ["quiz", "student"]

    def __str__(self):
        return f"{self.student.full_name} — {self.quiz.title}: {self.score}/{self.total}"

    @property
    def percent(self):
        try:
            return round(float(self.score) / float(self.total) * 100, 1) if float(self.total) else 0
        except Exception:
            return 0
