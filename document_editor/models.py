from django.conf import settings
from django.db import models


class DocumentTemplate(models.Model):
    CATEGORIES = [
        ("LETTRE", "Lettre administrative"),
        ("ATTESTATION", "Attestation"),
        ("CERTIFICAT", "Certificat"),
        ("BULLETIN", "Bulletin"),
        ("CONVOCATION", "Convocation"),
        ("CONTRAT", "Contrat"),
        ("RAPPORT", "Rapport"),
        ("PV", "Procès-verbal"),
        ("LISTE", "Liste des élèves"),
        ("RECU", "Reçu"),
    ]
    name = models.CharField("Nom du modèle", max_length=150)
    category = models.CharField("Catégorie", max_length=15, choices=CATEGORIES)
    header_text = models.CharField("En-tête", max_length=255, blank=True)
    footer_text = models.CharField("Pied de page", max_length=255, blank=True)
    watermark = models.CharField("Filigrane", max_length=100, blank=True)
    body_html = models.TextField("Contenu du modèle", blank=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Modèle de document"
        verbose_name_plural = "Modèles de documents"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.get_category_display()} — {self.name}"


class Document(models.Model):
    title = models.CharField("Titre", max_length=200)
    category = models.CharField("Catégorie", max_length=15, choices=DocumentTemplate.CATEGORIES)
    template = models.ForeignKey(
        DocumentTemplate, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="documents", verbose_name="Modèle utilisé",
    )
    body_html = models.TextField("Contenu")
    watermark = models.CharField("Filigrane", max_length=100, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="documents_created", verbose_name="Créé par",
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    updated_at = models.DateTimeField("Modifié le", auto_now=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title
