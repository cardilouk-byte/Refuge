from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from .models import Notification

User = get_user_model()


@login_required
def list_view(request):
    items = Notification.objects.filter(recipient=request.user)[:100]
    return render(request, "notifications/list.html", {"items": items})


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    if notification.recipient_id != request.user.pk:
        raise PermissionDenied
    if request.method == "POST":
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        if notification.url:
            return redirect(notification.url)
    return redirect("notifications:list")


@login_required
def mark_all(request):
    if request.method == "POST":
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect("notifications:list")
