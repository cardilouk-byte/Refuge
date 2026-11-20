from django.conf import settings
from django.db import models


class MediaFile(models.Model):
    class Category(models.TextChoices):
        ELEVES = "ELEVES", "Photos des élèves"
        ENSEIGNANTS = "ENSEIGNANTS", "Photos des enseignants"
        LOGO = "LOGO", "Logo et identité visuelle"
        SITE = "SITE", "Images du site vitrine"
        DOCUMENTS = "DOCUMENTS", "Documents"
        AUTRES = "AUTRES", "Autres"

    file = models.FileField("Fichier", upload_to="library/")
    original_name = models.CharField("Nom d'origine", max_length=255, blank=True)
    category = models.CharField("Catégorie", max_length=15, choices=Category.choices,
                                default=Category.AUTRES)
    width = models.PositiveIntegerField("Largeur", default=0)
    height = models.PositiveIntegerField("Hauteur", default=0)
    size_bytes = models.PositiveBigIntegerField("Taille (octets)", default=0)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="media_uploaded", verbose_name="Téléversé par",
    )
    created_at = models.DateTimeField("Ajouté le", auto_now_add=True)

    class Meta:
        verbose_name = "Fichier média"
        verbose_name_plural = "Bibliothèque de médias"
        ordering = ["-created_at"]

    def __str__(self):
        return self.original_name or self.file.name

    @property
    def is_image(self):
        return self.file.name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".gif"))

    @property
    def size_display(self):
        size = self.size_bytes
        for unit in ["o", "Ko", "Mo"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} Go"
