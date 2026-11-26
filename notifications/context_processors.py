from django.contrib.auth import get_user_model

from .models import Notification


def unread_count(request):
    data = {"unread_notifications": 0, "recent_notifications": []}
    try:
        if not request.user.is_authenticated:
            return data
        qs = Notification.objects.filter(recipient=request.user, is_read=False)
        data["unread_notifications"] = qs.count()
        data["recent_notifications"] = list(qs[:5])
    except Exception:
        pass
    return data
