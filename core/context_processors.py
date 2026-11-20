from .models import MenuItem, SiteSettings


def portal_counts(request):
    """Badge counts pou sidebar la (elèv aktif, pre-enskripsyon an atant)."""
    data = {"n_students": 0, "n_pending_pre": 0}
    try:
        user = request.user
        if user.is_authenticated and (user.is_school_staff or user.is_staff):
            from academics.models import ClassRoom
            from preregistration.models import PreRegistration
            from students.models import Student

            data["n_students"] = Student.objects.filter(status="ACTIF").count()
            data["n_pending_pre"] = PreRegistration.objects.filter(
                status__in=["SOUMET", "EGZAMEN"]
            ).count()
            data["n_classrooms"] = ClassRoom.objects.count()
    except Exception:
        pass
    return data


def site_info(request):
    menu = []
    for item in MenuItem.objects.filter(is_visible=True, parent__isnull=True):
        children = [child for child in item.children.filter(is_visible=True)]
        menu.append({"item": item, "children": children})
    return {
        "site_settings": SiteSettings.load(),
        "menu_items": menu,
    }
