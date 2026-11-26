from django import forms

from .models import BackupSettings


class BackupSettingsForm(forms.ModelForm):
    class Meta:
        model = BackupSettings
        fields = ["daily_enabled", "weekly_enabled", "monthly_enabled", "time_of_day",
                  "keep_last", "notify_email", "include_media"]
        widgets = {
            "time_of_day": forms.TimeInput(attrs={"type": "time"}, format="%H:%M"),
        }
