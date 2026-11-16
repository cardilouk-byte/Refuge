from django.contrib import admin
from django.contrib import messages
from django.http import FileResponse

from . import services
from .models import BackupRecord, BackupSettings


@admin.register(BackupSettings)
class BackupSettingsAdmin(admin.ModelAdmin):
    list_display = ("daily_enabled", "weekly_enabled", "monthly_enabled", "time_of_day", "keep_last")

    def has_add_permission(self, request):
        return not BackupSettings.objects.exists()


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = ("kind", "status", "filename", "size_display", "created_at", "created_by")
    list_filter = ("kind", "status")
    readonly_fields = ("kind", "status", "filename", "size_bytes", "checksum",
                       "includes_media", "created_by", "created_at", "note")

    @admin.action(description="Vérifier l'intégrité")
    def verify_action(self, request, queryset):
        for record in queryset:
            ok, message = services.verify_backup(record)
            messages.info(request, f"{record} : {message}")

    @admin.action(description="Télécharger le ZIP")
    def download_action(self, request, queryset):
        if queryset.count() != 1:
            messages.error(request, "Sélectionnez une seule sauvegarde à télécharger.")
            return
        path = services.BACKUP_DIR / queryset.first().filename
        if path.exists():
            return FileResponse(path.open("rb"), as_attachment=True)

    actions = [verify_action, download_action]
