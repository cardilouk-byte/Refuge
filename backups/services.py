import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

from django.conf import settings
from django.core import management
from django.core.mail import send_mail

from .models import BackupRecord, BackupSettings

BACKUP_DIR = Path(settings.BASE_DIR) / "backups_store"


def _notify_failure(subject, message):
    settings_obj = BackupSettings.load()
    recipient = settings_obj.notify_email or getattr(settings, "ADMIN_EMAIL_NOTIFICATION", "")
    if recipient:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)


def create_backup(kind=BackupRecord.Kind.MANUAL, user=None, note=""):
    settings_obj = BackupSettings.load()
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = date.today().strftime("%Y%m%d")
    record = BackupRecord(kind=kind, created_by=user, note=note,
                          includes_media=settings_obj.include_media)
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            data_file = tmp_path / "data.json"
            with open(data_file, "w", encoding="utf-8") as fh:
                management.call_command("dumpdata",
                                        exclude=["contenttypes", "sessions",
                                                 "auth.Permission", "admin.logentry"],
                                        indent=1, stdout=fh)

            zip_path = BACKUP_DIR / f"backup_{stamp}_{record.kind.lower()}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(data_file, "data.json")
                if settings_obj.include_media:
                    media_root = Path(settings.MEDIA_ROOT)
                    if media_root.exists():
                        for file_path in media_root.rglob("*"):
                            if file_path.is_file():
                                zf.write(file_path, f"media/{file_path.relative_to(media_root)}")

            record.filename = zip_path.name
            record.size_bytes = zip_path.stat().st_size
            record.checksum = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            record.status = BackupRecord.Status.SUCCESS
            record.save()

            _cleanup_old_backups(settings_obj.keep_last)
            return record
    except Exception as exc:
        record.status = BackupRecord.Status.FAILED
        record.note = (note + " | " if note else "") + str(exc)[:200]
        record.save()
        _notify_failure(
            "LNFCL : échec de sauvegarde",
            f"Une sauvegarde ({record.get_kind_display()}) a échoué : {exc}",
        )
        return record


def _cleanup_old_backups(keep_last):
    records = BackupRecord.objects.filter(status=BackupRecord.Status.SUCCESS)
    for record in records[keep_last:]:
        path = BACKUP_DIR / record.filename
        if path.exists():
            path.unlink()
        record.delete()


def verify_backup(record):
    path = BACKUP_DIR / record.filename
    if not path.exists():
        return False, "Fichier introuvable sur le serveur."
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != record.checksum:
        return False, "Empreinte SHA-256 différente : fichier corrompu."
    try:
        with zipfile.ZipFile(path) as zf:
            if "data.json" not in zf.namelist():
                return False, "Archive invalide : data.json absent."
            zf.read("data.json")
    except zipfile.BadZipFile:
        return False, "Archive ZIP invalide."
    return True, "Sauvegarde intègre et vérifiée."


def restore_backup(record, restore_media=True):
    path = BACKUP_DIR / record.filename
    if not path.exists():
        raise FileNotFoundError(path)
    ok, message = verify_backup(record)
    if not ok:
        raise ValueError(message)

    with zipfile.ZipFile(path) as zf:
        management.call_command("flush", "--noinput", verbosity=0)
        with tempfile.TemporaryDirectory() as tmp:
            data_file = Path(tmp) / "data.json"
            data_file.write_bytes(zf.read("data.json"))
            management.call_command("loaddata", str(data_file), verbosity=0)

        if restore_media and record.includes_media:
            media_root = Path(settings.MEDIA_ROOT)
            media_root.mkdir(exist_ok=True)
            for name in zf.namelist():
                if name.startswith("media/") and not name.endswith("/"):
                    target = media_root / name[len("media/"):]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(name) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
    return True
