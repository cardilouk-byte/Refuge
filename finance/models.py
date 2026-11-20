from django.conf import settings
from django.db import models


class FeeType(models.Model):
    name = models.CharField("Nom", max_length=100, help_text="Ex: Frais de scolarité, Uniforme")
    amount = models.DecimalField("Montant (HTG)", max_digits=10, decimal_places=2)
    school_year = models.ForeignKey(
        "academics.SchoolYear", on_delete=models.CASCADE,
        related_name="fee_types", verbose_name="Année scolaire",
    )
    description = models.CharField("Description", max_length=255, blank=True)

    class Meta:
        verbose_name = "Type de frais"
        verbose_name_plural = "Types de frais"
        ordering = ["school_year", "name"]

    def __str__(self):
        return f"{self.name} ({self.school_year.label})"


class Invoice(models.Model):
    class Status(models.TextChoices):
        IMPAYE = "IMPAYE", "Impayée"
        PARTIEL = "PARTIEL", "Partiellement payée"
        PAYE = "PAYE", "Payée"

    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE,
        related_name="invoices", verbose_name="Élève",
    )
    fee_type = models.ForeignKey(FeeType, on_delete=models.PROTECT, related_name="invoices", verbose_name="Type de frais")
    amount = models.DecimalField("Montant (HTG)", max_digits=10, decimal_places=2)
    due_date = models.DateField("Date d'échéance", blank=True, null=True)
    status = models.CharField("Statut", max_length=10, choices=Status.choices, default=Status.IMPAYE)
    created_at = models.DateTimeField("Créée le", auto_now_add=True)

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Facture #{self.pk} - {self.student.full_name} - {self.amount} HTG"

    @property
    def paid_amount(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def balance(self):
        return self.amount - self.paid_amount

    def update_status(self):
        paid = self.paid_amount
        if paid <= 0:
            self.status = self.Status.IMPAYE
        elif paid < self.amount:
            self.status = self.Status.PARTIEL
        else:
            self.status = self.Status.PAYE
        self.save(update_fields=["status"])


class Payment(models.Model):
    METHODS = [
        ("MONCASH", "MonCash"), ("NATCASH", "NatCash"), ("ESPECES", "Espèces"),
        ("BANQUE", "Virement bancaire"), ("CHEQUE", "Chèque"),
    ]
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments", verbose_name="Facture")
    amount = models.DecimalField("Montant (HTG)", max_digits=10, decimal_places=2)
    method = models.CharField("Méthode", max_length=10, choices=METHODS, default="ESPECES")
    reference = models.CharField("Référence", max_length=100, blank=True)
    paid_at = models.DateTimeField("Payé le", auto_now_add=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="payments_received", verbose_name="Reçu par",
    )

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ["-paid_at"]

    def __str__(self):
        return f"Paiement #{self.pk} - {self.amount} HTG ({self.get_method_display()})"

    @property
    def receipt_number(self):
        return f"REC-{self.pk:06d}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.invoice.update_status()


class Expense(models.Model):
    CATEGORIES = [
        ("SALAIRE", "Salaires"),
        ("FOURNITURES", "Fournitures"),
        ("ENTRETIEN", "Entretien / électricité"),
        ("TRANSPORT", "Transport"),
        ("AUTRE", "Autre"),
    ]

    label = models.CharField("Libellé", max_length=200)
    category = models.CharField("Catégorie", max_length=20, choices=CATEGORIES, default="AUTRE")
    amount = models.DecimalField("Montant (HTG)", max_digits=12, decimal_places=2)
    spent_at = models.DateField("Date", null=True, blank=True)
    note = models.CharField("Note", max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True,
        related_name="expenses_recorded", verbose_name="Créé par",
    )
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ["-spent_at", "-created_at"]

    def __str__(self):
        return f"{self.label} — {self.amount} HTG"
