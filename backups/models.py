from django.conf import settings
from django.db import models


class BackupSettings(models.Model):
    FREQUENCIES = [
        ("DAILY", "Chaque jour"),
        ("WEEKLY", "Chaque semaine"),
        ("MONTHLY", "Chaque mois"),
    ]
    daily_enabled = models.BooleanField("Backup quotidien", default=True)
    weekly_enabled = models.BooleanField("Backup hebdomadaire", default=True)
    monthly_enabled = models.BooleanField("Backup mensuel", default=False)
    time_of_day = models.TimeField("Heure du backup", default="02:00")
    keep_last = models.PositiveIntegerField("Nombre de backups à conserver", default=30)
    notify_email = models.EmailField("Email de notification", blank=True)
    include_media = models.BooleanField("Inclure les fichiers (media)", default=True)

    class Meta:
        verbose_name = "Paramètres de sauvegarde"
        verbose_name_plural = "Paramètres de sauvegarde"

    def __str__(self):
        return "Configuration des sauvegardes"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class BackupRecord(models.Model):
    class Kind(models.TextChoices):
        MANUAL = "MANUAL", "Manuel"
        DAILY = "DAILY", "Automatique (jour)"
        WEEKLY = "WEEKLY", "Automatique (semaine)"
        MONTHLY = "MONTHLY", "Automatique (mois)"

    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Réussi"
        FAILED = "FAILED", "Échoué"

    kind = models.CharField("Type", max_length=10, choices=Kind.choices, default=Kind.MANUAL)
    status = models.CharField("Statut", max_length=10, choices=Status.choices, default=Status.SUCCESS)
    filename = models.CharField("Fichier", max_length=255, blank=True)
    size_bytes = models.PositiveBigIntegerField("Taille (octets)", default=0)
    checksum = models.CharField("Empreinte SHA-256", max_length=64, blank=True)
    includes_media = models.BooleanField("Fichiers inclus", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="backups_created", verbose_name="Créé par",
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)
    note = models.CharField("Note", max_length=255, blank=True)

    class Meta:
        verbose_name = "Sauvegarde"
        verbose_name_plural = "Sauvegardes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.created_at:%d/%m/%Y %H:%M} ({self.get_status_display()})"

    @property
    def size_display(self):
        size = self.size_bytes
        for unit in ["o", "Ko", "Mo", "Go"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} To"
