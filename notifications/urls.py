from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.list_view, name="list"),
    path("lu/<int:pk>/", views.mark_read, name="mark_read"),
    path("tout-lu/", views.mark_all, name="mark_all"),
]
