from django import forms

from academics.models import ClassRoom

from .models import Question, Quiz


class QuizForm(forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["classroom", "class_subject", "title", "description", "due_date", "is_published"]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_subject"].required = False
        self.fields["classroom"].queryset = ClassRoom.objects.select_related("level", "school_year").order_by(
            "school_year__label", "level__order", "section"
        )
        if user and not (user.is_staff or getattr(user, "is_school_staff", False)):
            self.fields["classroom"].queryset = ClassRoom.objects.filter(
                subjects__teacher__user=user
            ).distinct().select_related("level", "school_year")


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "option_a", "option_b", "option_c", "option_d", "correct", "points", "order"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2})}
