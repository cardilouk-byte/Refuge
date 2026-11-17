from django.conf import settings
from django.db import models


class Book(models.Model):
    title = models.CharField("Titre", max_length=200)
    author = models.CharField("Auteur", max_length=150, blank=True)
    isbn = models.CharField("ISBN", max_length=30, blank=True)
    category = models.CharField("Catégorie", max_length=100, default="Général")
    description = models.TextField("Description", blank=True)
    total_copies = models.PositiveIntegerField("Nombre d'exemplaires", default=1)
    created_at = models.DateTimeField("Ajouté le", auto_now_add=True)

    class Meta:
        verbose_name = "Livre"
        verbose_name_plural = "Livres"
        ordering = ["title"]

    def __str__(self):
        return self.title

    @property
    def active_loans(self):
        return self.loans.filter(returned_at__isnull=True)

    @property
    def available_copies(self):
        return max(0, self.total_copies - self.active_loans.count())


class Loan(models.Model):
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="loans", verbose_name="Livre",
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="loans", verbose_name="Élève",
    )
    borrowed_at = models.DateField("Date d'emprunt", auto_now_add=True)
    due_date = models.DateField("Retour prévu")
    returned_at = models.DateField("Retourné le", blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="loans_crees", verbose_name="Créé par",
    )

    class Meta:
        verbose_name = "Emprunt"
        verbose_name_plural = "Emprunts"
        ordering = ["-borrowed_at"]

    def __str__(self):
        return f"{self.book.title} — {self.student}"

    @property
    def is_late(self):
        from django.utils import timezone
        return self.returned_at is None and self.due_date < timezone.localdate()
