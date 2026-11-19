from django import forms

from academics.models import ClassSubject

from .models import LessonEntry


class LessonEntryForm(forms.ModelForm):
    class Meta:
        model = LessonEntry
        fields = ["class_subject", "date", "content"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "content": forms.Textarea(attrs={"rows": 5, "placeholder": "Sa ou dekri nan kout la, paj lej, egzesis…"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        qs = ClassSubject.objects.select_related("classroom", "subject").order_by(
            "classroom__school_year", "classroom__level__order"
        )
        if user and not (user.is_staff or getattr(user, "is_school_staff", False)):
            qs = qs.filter(teacher__user=user)
        self.fields["class_subject"].queryset = qs
