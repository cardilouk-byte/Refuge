from django import forms

from .models import Department, StaffPosition


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            "name", "code", "kind", "parent", "head_title", "description",
            "email", "phone", "location", "order", "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "kind": forms.Select(attrs={"class": "form-select"}),
            "parent": forms.Select(attrs={"class": "form-select"}),
            "head_title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class StaffPositionForm(forms.ModelForm):
    class Meta:
        model = StaffPosition
        fields = ["department", "title", "user", "teacher", "external_name", "is_head", "order"]
        widgets = {
            "department": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "user": forms.Select(attrs={"class": "form-select"}),
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "external_name": forms.TextInput(attrs={"class": "form-control"}),
            "is_head": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()
        if not (cleaned.get("user") or cleaned.get("teacher") or cleaned.get("external_name")):
            raise forms.ValidationError("Chwazi yon itilizatè, yon pwofesè, oswa antre yon nom.")
        return cleaned
