from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Votre nom", "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control", "placeholder": "Votre email", "required": True,
            }),
            "subject": forms.TextInput(attrs={
                "class": "form-control", "placeholder": "Sujet", "required": True,
            }),
            "message": forms.Textarea(attrs={
                "class": "form-control", "placeholder": "Votre message", "rows": 5, "required": True,
            }),
        }
