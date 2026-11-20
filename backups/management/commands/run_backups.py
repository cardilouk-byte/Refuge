from datetime import date

from django.core.management.base import BaseCommand

from backups import services
from backups.models import BackupRecord, BackupSettings


class Command(BaseCommand):
    help = "Exécute les backups automatiques dus (jour / semaine / mois)."

    def handle(self, *args, **options):
        settings_obj = BackupSettings.load()
        today = date.today()

        due = []
        if settings_obj.daily_enabled:
            due.append(BackupRecord.Kind.DAILY)
        if settings_obj.weekly_enabled and today.weekday() == 0:
            due.append(BackupRecord.Kind.WEEKLY)
        if settings_obj.monthly_enabled and today.day == 1:
            due.append(BackupRecord.Kind.MONTHLY)

        for kind in due:
            if self._already_ran_today(kind):
                continue
            record = services.create_backup(kind=kind, note="Backup automatique")
            self.stdout.write(f"{kind} : {record.get_status_display()}")

    def _already_ran_today(self, kind):
        return BackupRecord.objects.filter(
            kind=kind, status=BackupRecord.Status.SUCCESS,
            created_at__date=date.today(),
        ).exists()
