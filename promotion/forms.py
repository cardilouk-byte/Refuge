from django import forms

from academics.models import SchoolYear


class NewYearForm(forms.Form):
    label = forms.CharField(
        label="Annè ki prale a",
        max_length=20,
        help_text="Ex: 2026-2027",
    )
    copy_classrooms = forms.BooleanField(
        label="Kopi klas yo, matye yo ak pwofesè yo nan annè nèf la",
        required=False,
        initial=True,
    )

    def clean_label(self):
        label = self.cleaned_data["label"].strip()
        if SchoolYear.objects.filter(label=label).exists():
            raise forms.ValidationError("Annè sa a deja egziste.")
        return label
