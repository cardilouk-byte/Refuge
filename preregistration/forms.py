from django import forms

from academics.models import Level


class StudentStepForm(forms.Form):
    first_name = forms.CharField(label="Prénom de l'élève", max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label="Nom de l'élève", max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    gender = forms.ChoiceField(label="Sexe", choices=[("M", "Masculin"), ("F", "Féminin")], widget=forms.Select(attrs={"class": "form-select"}))
    birth_date = forms.DateField(label="Date de naissance", widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}))
    birth_place = forms.CharField(label="Lieu de naissance", max_length=150, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    address = forms.CharField(label="Adresse", max_length=255, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    photo = forms.ImageField(label="Photo de l'élève (opsyonèl)", required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))


class ParentStepForm(forms.Form):
    parent_name = forms.CharField(label="Nom du parent / responsable", max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    parent_relation = forms.ChoiceField(
        label="Relation avec l'élève",
        choices=[("PERE", "Père"), ("MERE", "Mère"), ("TUTEUR", "Tuteur / Responsable")],
        initial="TUTEUR", widget=forms.Select(attrs={"class": "form-select"}),
    )
    parent_phone = forms.CharField(label="Téléphone", max_length=50, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: +509 37 00 0000"}))
    parent_email = forms.EmailField(label="Email (opsyonèl)", required=False, widget=forms.EmailInput(attrs={"class": "form-control"}))
    parent_profession = forms.CharField(label="Profession (opsyonèl)", max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))


class SchoolStepForm(forms.Form):
    desired_level = forms.ModelChoiceField(label="Niveau souhaité", queryset=Level.objects.all(), required=False, widget=forms.Select(attrs={"class": "form-select"}))
    previous_school = forms.CharField(label="École précédente (opsyonèl)", max_length=200, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_class = forms.CharField(label="Dernière classe fréquentée (opsyonèl)", max_length=100, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    birth_certificate = forms.FileField(label="Acte de naissance (opsyonèl)", required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    report_card = forms.FileField(label="Bulletin précédent (opsyonèl)", required=False, widget=forms.ClearableFileInput(attrs={"class": "form-control"}))
    notes = forms.CharField(label="Notes / informations supplémentaires (opsyonèl)", required=False, widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}))
