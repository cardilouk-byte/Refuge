from django import forms

from .models import CarnetSettings


class BootstrapMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if widget.__class__.__name__ in ("CheckboxInput",):
                widget.attrs.setdefault("class", "form-check-input")
            elif widget.__class__.__name__ in ("Select", "SelectMultiple"):
                widget.attrs.setdefault("class", "form-select")
            else:
                widget.attrs.setdefault("class", "form-control")


class CarnetSettingsForm(BootstrapMixin, forms.ModelForm):
    class Meta:
        model = CarnetSettings
        fields = [
            "school_name", "slogan", "subtitle", "address", "tel1", "tel2",
            "email", "footer_motto", "reglements_text", "show_graph",
            "directeur", "border_color", "cover_bg", "cover_text",
            "header_color", "show_photo",
        ]
        widgets = {
            "reglements_text": forms.Textarea(attrs={"rows": 10}),
            "border_color": forms.TextInput(attrs={"type": "color", "style": "width:64px;height:38px;padding:.1rem"}),
            "cover_bg": forms.TextInput(attrs={"type": "color", "style": "width:64px;height:38px;padding:.1rem"}),
            "cover_text": forms.TextInput(attrs={"type": "color", "style": "width:64px;height:38px;padding:.1rem"}),
            "header_color": forms.TextInput(attrs={"type": "color", "style": "width:64px;height:38px;padding:.1rem"}),
        }
