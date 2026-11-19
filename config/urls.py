from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve as static_serve

from config.settings import ADMIN_URL

urlpatterns = [
    path(ADMIN_URL, admin.site.urls),
    path("comptes/", include("accounts.urls")),
    path("", include("dashboard.urls")),
    path("", include("departments.urls")),
    path("", include("preregistration.urls")),
    path("", include("portals.urls")),
    path("", include("backups.urls")),
    path("", include("document_editor.urls")),
    path("", include("excel_manager.urls")),
    path("", include("media_library.urls")),
    path("devoirs/", include("homework.urls")),
    path("examens/", include("exams.urls")),
    path("notes/", include("grades.urls")),
    path("presens/", include("attendance.urls")),
    path("bibliotheque/", include("library.urls")),
    path("", include("students.urls")),
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r"^media/(?P<path>.*)$", static_serve, {"document_root": settings.MEDIA_ROOT}),
    ]

admin.site.site_header = "LNFCL — Panneau de contrôle"
admin.site.site_title = "LNFCL"
admin.site.index_title = "Gestion du contenu et de l'école"
