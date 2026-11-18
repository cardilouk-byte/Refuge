from .models import MenuItem, SiteSettings


def site_info(request):
    menu = []
    for item in MenuItem.objects.filter(is_visible=True, parent__isnull=True):
        children = [child for child in item.children.filter(is_visible=True)]
        menu.append({"item": item, "children": children})
    return {
        "site_settings": SiteSettings.load(),
        "menu_items": menu,
    }
