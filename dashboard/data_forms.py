from django import forms

from academics.models import ClassRoom, ClassSubject, Cycle, Level, Period, SchoolYear, Subject
from teachers.models import Teacher


class SchoolYearForm(forms.ModelForm):
    class Meta:
        model = SchoolYear
        fields = ["label", "is_current"]
        labels = {"label": "Libèl (ex: 2025-2026)", "is_current": "Nan kour"}


class CycleForm(forms.ModelForm):
    class Meta:
        model = Cycle
        fields = ["name", "order"]
        labels = {"name": "Non (ex: Fonmantal)", "order": "Lòd"}


class LevelForm(forms.ModelForm):
    class Meta:
        model = Level
        fields = ["name", "cycle", "order"]
        labels = {"name": "Non (ex: 6èm AF, NS1)", "cycle": "Sik", "order": "Lòd"}


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ["school_year", "name", "order"]
        labels = {"school_year": "Ane skolè", "name": "Non (ex: Trimestre 1)", "order": "Lòd"}


class ClassRoomForm(forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = ["school_year", "level", "section", "main_teacher"]
        labels = {"school_year": "Ane skolè", "level": "Nivo", "section": "Seksyon", "main_teacher": "Profesè titulè"}


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code"]
        labels = {"name": "Non (ex: Matematik)", "code": "Kòd"}


class TeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ["first_name", "last_name", "matricule", "specialty", "phone", "email", "photo", "hired_at"]
        labels = {
            "first_name": "Pwòm", "last_name": "Non", "matricule": "Matrikil (ex: PROF-001)",
            "specialty": "Espesyalite", "phone": "Telefòn", "email": "Imèl",
            "photo": "Foto", "hired_at": "Dat anbouch",
        }
        widgets = {"hired_at": forms.DateInput(attrs={"type": "date"})}
        help_texts = {"matricule": "Otomatik si ou kite l vid."}


class ClassSubjectForm(forms.ModelForm):
    class Meta:
        model = ClassSubject
        fields = ["classroom", "subject", "teacher", "coefficient", "weekly_hours"]
        labels = {"classroom": "Klas", "subject": "Matyè", "teacher": "Profesè", "coefficient": "Koyefisyan", "weekly_hours": "Èdtan/psemèn"}


def _generate_teacher_password(length: int = 8) -> str:
    import random
    import string

    chars = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(chars) for _ in range(length))
