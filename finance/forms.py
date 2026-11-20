from datetime import date

from django import forms

from students.models import Student

from .models import Expense, FeeType, Invoice, Payment


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ["student", "fee_type", "amount", "due_date"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("amount"):
            fee = cleaned.get("fee_type")
            if fee:
                cleaned["amount"] = fee.amount
        return cleaned


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "reference"]
        labels = {"amount": "Montant (HTG)", "method": "M\u00e9thode", "reference": "R\u00e9f\u00e9rence (MonCash, ch\u00e8que...)"}


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["label", "category", "amount", "spent_at", "note"]
        labels = {"label": "Libell\u00e9", "category": "Cat\u00e9gorie", "amount": "Montant (HTG)", "spent_at": "Date", "note": "Note"}
        widgets = {"spent_at": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["spent_at"].initial = date.today()
