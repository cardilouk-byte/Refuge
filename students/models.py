from django.conf import settings
from django.db import models


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIF = "ACTIF", "Actif"
        TRANSFERE = "TRANSFERE", "Transféré"
        ARCHIVE = "ARCHIVE", "Archivé"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="student_profile", verbose_name="Compte utilisateur",
    )
    matricule = models.CharField("Matricule", max_length=20, unique=True)
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    birth_date = models.DateField("Date de naissance", blank=True, null=True)
    gender = models.CharField("Sexe", max_length=1, choices=[("M", "Masculin"), ("F", "Féminin")], blank=True)
    photo = models.ImageField("Photo", upload_to="students/", blank=True, null=True)
    nis = models.CharField("NIS", max_length=30, blank=True)
    ninu = models.CharField("NINU", max_length=30, blank=True)
    classroom = models.ForeignKey(
        "academics.ClassRoom", on_delete=models.SET_NULL, blank=True, null=True,
        related_name="students", verbose_name="Classe",
    )
    status = models.CharField("Statut", max_length=10, choices=Status.choices, default=Status.ACTIF)
    address = models.CharField("Adresse", max_length=255, blank=True)
    enrolled_at = models.DateField("Date d'inscription", auto_now_add=True)

    class Meta:
        verbose_name = "Élève"
        verbose_name_plural = "Élèves"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.matricule})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Parent(models.Model):
    RELATIONS = [
        ("PERE", "Père"), ("MERE", "Mère"), ("TUTEUR", "Tuteur"), ("AUTRE", "Autre"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="parent_profile", verbose_name="Compte utilisateur",
    )
    first_name = models.CharField("Prénom", max_length=100)
    last_name = models.CharField("Nom", max_length=100)
    relation = models.CharField("Relation", max_length=10, choices=RELATIONS, default="TUTEUR")
    phone = models.CharField("Téléphone", max_length=50, blank=True)
    email = models.EmailField("Email", blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    students = models.ManyToManyField(
        "students.Student", through="ParentStudent", related_name="parents", verbose_name="Enfants"
    )

    class Meta:
        verbose_name = "Parent / Responsable"
        verbose_name_plural = "Parents / Responsables"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class ParentStudent(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, verbose_name="Parent")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name="Élève")
    is_primary = models.BooleanField("Responsable principal", default=False)

    class Meta:
        verbose_name = "Lien parent-élève"
        verbose_name_plural = "Liens parent-élève"
        unique_together = ["parent", "student"]
