from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN = "SUPERADMIN", "Super Administrateur"
        DIRECTION = "DIRECTION", "Direction"
        ENSEIGNANT = "ENSEIGNANT", "Professeur"
        ELEVE = "ELEVE", "Élève"
        PARENT = "PARENT", "Parent"

    role = models.CharField("Rôle", max_length=20, choices=Role.choices, default=Role.SUPERADMIN)

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_school_staff(self):
        return self.role in (self.Role.SUPERADMIN, self.Role.DIRECTION)

    @property
    def is_teaching_staff(self):
        return self.is_school_staff or self.role == self.Role.ENSEIGNANT

    @property
    def dashboard_url(self):
        return {
            self.Role.SUPERADMIN: reverse("dashboard:home"),
            self.Role.DIRECTION: reverse("dashboard:home"),
            self.Role.ENSEIGNANT: reverse("portals:professeur"),
            self.Role.ELEVE: reverse("portals:eleve"),
            self.Role.PARENT: reverse("portals:parent"),
        }.get(self.role, reverse("home"))
