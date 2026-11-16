from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import ContactMessage


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ("username",)


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
