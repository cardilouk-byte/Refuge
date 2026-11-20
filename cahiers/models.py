from django.conf import settings
from django.db import models


class LessonEntry(models.Model):
    class Status(models.TextChoices):
        ATTENTE = "ATTENTE", "An atant"
        VALIDE = "VALIDE", "Verifye"
        REJETE = "REJETE", "Rekite"

    class_subject = models.ForeignKey(
        "academics.ClassSubject", on_delete=models.CASCADE,
        related_name="lessons", verbose_name="Matiye (klas)",
    )
    date = models.DateField("Dat")
    content = models.TextField("Sa ki fèt nan kout la")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="lessons_written", verbose_name="Ekri pa",
    )
    created_at = models.DateTimeField("Kreye le", auto_now_add=True)
    status = models.CharField("Estati verification", max_length=10, choices=Status.choices, default=Status.ATTENTE)
    review_comment = models.CharField("Remak Direction", max_length=255, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="lessons_reviewed", verbose_name="Verifye pa",
    )

    class Meta:
        verbose_name = "Cahier de tèks"
        verbose_name_plural = "Cahiers de tèks"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.class_subject} — {self.date:%d/%m/%Y}"
