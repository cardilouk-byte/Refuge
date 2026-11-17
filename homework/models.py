from django.conf import settings
from django.db import models


class Devoir(models.Model):
    classroom = models.ForeignKey(
        "academics.ClassRoom", on_delete=models.CASCADE,
        related_name="devoirs", verbose_name="Classe",
    )
    subject = models.ForeignKey(
        "academics.Subject", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="devoirs", verbose_name="Matière",
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="devoirs", verbose_name="Professeur",
    )
    title = models.CharField("Titre", max_length=200)
    description = models.TextField("Consignes", blank=True)
    assigned_date = models.DateField("Date donnée", auto_now_add=True)
    due_date = models.DateField("Date de remise")
    fichier = models.FileField(
        "Fichier joint", upload_to="devoirs/", blank=True, null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="devoirs_crees", verbose_name="Créé par",
    )

    class Meta:
        verbose_name = "Devoir"
        verbose_name_plural = "Devoirs"
        ordering = ["-due_date"]

    def __str__(self):
        return f"{self.title} — {self.classroom}"
