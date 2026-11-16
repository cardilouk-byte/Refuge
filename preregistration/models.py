import uuid

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class PreRegistration(models.Model):
    STEPS = [
        ("BROUILLON", "Boullon"),
        ("SOUMET", "Soumèt"),
        ("EGZAMEN", "An egzamen"),
        ("ACCEPTE", "Asepte"),
        ("REFUSE", "Rejte"),
        ("INSCRIT", "Inskri (konvèti)"),
    ]
    reference = models.CharField("Référence", max_length=20, unique=True, editable=False)
    status = models.CharField(
        "Statut", max_length=10, choices=STEPS, default="SOUMET",
    )

    first_name = models.CharField("Prénom de l'élève", max_length=100)
    last_name = models.CharField("Nom de l'élève", max_length=100)
    gender = models.CharField("Sexe", max_length=1, choices=[("M", "Masculin"), ("F", "Féminin")])
    birth_date = models.DateField("Date de naissance")
    birth_place = models.CharField("Lieu de naissance", max_length=150, blank=True)
    address = models.CharField("Adresse", max_length=255, blank=True)
    photo = models.ImageField("Photo de l'élève", upload_to="preinscription/", blank=True, null=True)

    desired_level = models.ForeignKey(
        "academics.Level", verbose_name="Niveau souhaité", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="pre_registrations",
    )
    previous_school = models.CharField("École précédente", max_length=200, blank=True)
    last_class = models.CharField("Dernière classe fréquentée", max_length=100, blank=True)

    parent_name = models.CharField("Nom du parent / responsable", max_length=150)
    parent_relation = models.CharField(
        "Relation", max_length=20,
        choices=[("PÈ", "Père"), ("MÈ", "Mère"), ("TUTEUR", "Tuteur / Responsable")],
        default="TUTEUR",
    )
    parent_phone = models.CharField("Téléphone", max_length=50)
    parent_email = models.EmailField("Email", blank=True)
    parent_profession = models.CharField("Profession", max_length=100, blank=True)

    birth_certificate = models.FileField(
        "Acte de naissance", upload_to="preinscription/documents/", blank=True, null=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
    )
    report_card = models.FileField(
        "Bulletin précédent", upload_to="preinscription/documents/", blank=True, null=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
    )

    notes = models.TextField("Notes / observations", blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Traité par", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reviewed_pre_registrations",
    )
    reviewed_at = models.DateTimeField("Date de traitement", null=True, blank=True)
    converted_student = models.ForeignKey(
        "students.Student", verbose_name="Élève créé", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="from_pre_registration",
    )
    created_at = models.DateTimeField("Date de soumission", auto_now_add=True)

    class Meta:
        verbose_name = "Pré-inscription"
        verbose_name_plural = "Pré-inscriptions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"PRE-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
