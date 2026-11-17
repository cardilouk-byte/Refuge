from django.db import models


class Exam(models.Model):
    classroom = models.ForeignKey(
        "academics.ClassRoom", on_delete=models.CASCADE,
        related_name="exams", verbose_name="Classe",
    )
    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.CASCADE,
        related_name="exams", verbose_name="Matière",
    )
    period = models.ForeignKey(
        "academics.Period", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="exams", verbose_name="Période",
    )
    title = models.CharField("Titre", max_length=200)
    exam_date = models.DateField("Date de l'examen")
    start_time = models.TimeField("Heure de début", blank=True, null=True)
    duration_minutes = models.PositiveIntegerField("Durée (minutes)", default=60)
    max_score = models.PositiveIntegerField("Note maximale", default=20)
    coefficient = models.PositiveSmallIntegerField("Coefficient", default=1)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Examen"
        verbose_name_plural = "Examens"
        ordering = ["-exam_date"]

    def __str__(self):
        return f"{self.title} — {self.classroom} ({self.exam_date})"
