from functools import wraps

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.is_staff or request.user.role in roles:
                return view(request, *args, **kwargs)
            raise PermissionDenied
        return wrapped
    return decorator


def dashboard_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff or request.user.is_school_staff:
            return view(request, *args, **kwargs)
        raise PermissionDenied
    return wrapped


def direction_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff or request.user.role in (request.user.Role.SUPERADMIN, request.user.Role.DIRECTION):
            return view(request, *args, **kwargs)
        raise PermissionDenied
    return wrapped


def staff_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff or request.user.is_school_staff:
            return view(request, *args, **kwargs)
        raise PermissionDenied
    return wrapped


def teaching_staff_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff or request.user.is_teaching_staff:
            return view(request, *args, **kwargs)
        raise PermissionDenied
    return wrapped


def superadmin_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_superuser or request.user.role == "SUPERADMIN":
            return view(request, *args, **kwargs)
        raise PermissionDenied
    return wrapped


@login_required
def role_home(request):
    return redirect(request.user.dashboard_url)
