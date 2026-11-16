from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from config.settings import get_env

ADMIN_URL = get_env("ADMIN_URL", "kontwol/").strip("/") + "/"

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path("comptes/", include("accounts.urls")),
    path("", include("dashboard.urls")),
    path("", include("portals.urls")),
    path("", include("backups.urls")),
    path("", include("document_editor.urls")),
    path("", include("excel_manager.urls")),
    path("", include("media_library.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = "LNFCL — Panneau de contrôle"
admin.site.site_title = "LNFCL"
admin.site.index_title = "Gestion du contenu et de l'école"
