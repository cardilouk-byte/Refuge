from django.contrib.auth import get_user_model

from .models import Notification


def unread_count(request):
    try:
        if not request.user.is_authenticated:
            return {"unread_notifications": 0}
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {"unread_notifications": count}
    except Exception:
        return {"unread_notifications": 0}
