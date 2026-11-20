from django.contrib import messages
from django.http import FileResponse
from django.shortcuts import redirect, render

from accounts.views import staff_required, superadmin_required

from . import services
from .forms import BackupSettingsForm
from .models import BackupRecord, BackupSettings


@staff_required
def index(request):
    records = BackupRecord.objects.all()[:50]
    return render(request, "backups/index.html", {
        "records": records,
        "settings_obj": BackupSettings.load(),
    })


@superadmin_required
def create_manual(request):
    if request.method == "POST":
        record = services.create_backup(
            kind=BackupRecord.Kind.MANUAL, user=request.user,
            note=request.POST.get("note", ""),
        )
        if record.status == BackupRecord.Status.SUCCESS:
            messages.success(request, "Sauvegarde créée avec succès.")
        else:
            messages.error(request, f"Échec de la sauvegarde : {record.note}")
    return redirect("backups:index")


@superadmin_required
def download(request, pk):
    record = BackupRecord.objects.get(pk=pk)
    path = services.BACKUP_DIR / record.filename
    if not path.exists():
        messages.error(request, "Fichier de sauvegarde introuvable.")
        return redirect("backups:index")
    return FileResponse(path.open("rb"), as_attachment=True)


@superadmin_required
def verify(request, pk):
    record = BackupRecord.objects.get(pk=pk)
    ok, message = services.verify_backup(record)
    messages.info(request, f"{record} : {message}")
    return redirect("backups:index")


@superadmin_required
def restore(request, pk):
    record = BackupRecord.objects.get(pk=pk)
    if request.method == "POST":
        try:
            services.restore_backup(record, restore_media=request.POST.get("media") == "on")
            messages.success(request, "Restauration terminée avec succès.")
        except Exception as exc:
            messages.error(request, f"Échec de la restauration : {exc}")
    return redirect("backups:index")


@superadmin_required
def import_backup_file(request):
    uploaded = request.FILES.get("backup_file")
    if request.method != "POST" or uploaded is None:
        messages.error(request, "Chwazi yon fichye backup ZIP (.zip) pou w importe.")
        return redirect("backups:index")
    if not uploaded.name.lower().endswith(".zip"):
        messages.error(request, "Fichye a dwe yon ZIP (backup LNFCL).")
        return redirect("backups:index")
    restore_media = request.POST.get("media") == "on"
    try:
        target = services.import_backup(uploaded, restore_media=restore_media)
    except Exception as exc:
        messages.error(request, f"Import echwe : {exc}")
        return redirect("backups:index")
    services.register_imported_backup(target.name, user=request.user, restore_media=restore_media)
    messages.success(request, f"Backup {uploaded.name} importe epi restore av\u00e8k siks\u00e8. Ou ka bezwen konekte ank\u00f2.")
    return redirect("backups:index")


@superadmin_required
def settings_view(request):
    settings_obj = BackupSettings.load()
    if request.method == "POST":
        form = BackupSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Paramètres de sauvegarde enregistrés.")
            return redirect("backups:index")
    else:
        form = BackupSettingsForm(instance=settings_obj)
    return render(request, "backups/settings.html", {"form": form})
