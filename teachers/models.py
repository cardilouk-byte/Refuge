from django.conf import settings
from django.db import models


class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="teacher_profile", verbose_name="Compte utilisateur",
    )
    matricule = models.CharField("Matricule", max_length=20, unique=True)
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    specialty = models.CharField("Spécialité", max_length=150, blank=True)
    phone = models.CharField("Téléphone", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    photo = models.ImageField("Photo", upload_to="teachers/", blank=True, null=True)
    hired_at = models.DateField("Date d'embauche", blank=True, null=True)

    class Meta:
        verbose_name = "Professeur"
        verbose_name_plural = "Professeurs"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
