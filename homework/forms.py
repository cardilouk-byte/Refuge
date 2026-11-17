from django import forms

from academics.models import ClassRoom, Subject

from .models import Devoir


class DevoirForm(forms.ModelForm):
    class Meta:
        model = Devoir
        fields = ["classroom", "subject", "title", "description", "due_date", "fichier"]
        widgets = {
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
