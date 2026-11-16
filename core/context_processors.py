from .models import MenuItem, SiteSettings


def site_info(request):
    return {
        "site_settings": SiteSettings.load(),
        "menu_items": MenuItem.objects.filter(is_visible=True),
    }
