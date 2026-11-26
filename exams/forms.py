from django import forms

from .models import Exam


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ["classroom", "subject", "period", "title", "exam_date", "start_time", "duration_minutes", "max_score", "coefficient"]
        widgets = {
            "classroom": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "period": forms.Select(attrs={"class": "form-select"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "exam_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "duration_minutes": forms.NumberInput(attrs={"class": "form-control"}),
            "max_score": forms.NumberInput(attrs={"class": "form-control"}),
            "coefficient": forms.NumberInput(attrs={"class": "form-control"}),
        }
