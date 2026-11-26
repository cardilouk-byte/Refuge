import secrets
import string

from django import forms

from students.models import Student


def generate_password(length=8):
    alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "matricule", "first_name", "last_name", "birth_date", "gender",
            "classroom", "status", "address", "photo", "nis", "ninu",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "matricule": "Matricule", "first_name": "Prenom", "last_name": "Non",
            "birth_date": "Dat nesans", "gender": "Sèks", "classroom": "Klas",
            "status": "Estati", "address": "Adrès", "photo": "Foto",
            "nis": "NIS", "ninu": "NINU",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from academics.models import ClassRoom

        self.fields["classroom"].queryset = ClassRoom.objects.select_related(
            "level", "school_year"
        ).order_by("school_year__label", "level__order", "section")
        self.fields["status"].required = False
        self.fields["photo"].required = False
        self.fields["gender"].required = False
        self.fields["nis"].required = False
        self.fields["ninu"].required = False
