from django.urls import path

from . import views

app_name = "backups"

urlpatterns = [
    path("backup/", views.index, name="index"),
    path("backup/creer/", views.create_manual, name="create"),
    path("backup/<int:pk>/telecharger/", views.download, name="download"),
    path("backup/<int:pk>/verifier/", views.verify, name="verify"),
    path("backup/<int:pk>/restaurer/", views.restore, name="restore"),
    path("backup/parametres/", views.settings_view, name="settings"),
    path("backup/importer/", views.import_backup_file, name="import"),
]
