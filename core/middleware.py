from django.shortcuts import render

from config.settings import ADMIN_URL


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        chemins_toujours_ouverts = (
            f"/{ADMIN_URL}",
            "/static/",
            "/media/",
            "/connexion/",
            "/deconnexion/",
            "/preinscription/",
        )

        if request.path.startswith(chemins_toujours_ouverts):
            return self.get_response(request)

        try:
            from core.models import SiteSettings
            site_settings = SiteSettings.load()
        except Exception:
            site_settings = None

        if site_settings and not site_settings.site_actif:
            user = getattr(request, "user", None)
            if not (user and user.is_authenticated and (user.is_staff or user.is_superuser)):
                return render(
                    request,
                    "base/maintenance.html",
                    {"site_settings": site_settings, "message": site_settings.message_maintenance},
                    status=503,
                )

        return self.get_response(request)
