from django.urls import path

from . import badge_views

app_name = "students"

urlpatterns = [
    path("badge/", badge_views.badge_own, name="badge_own"),
    path("eleves/<int:pk>/badge/", badge_views.badge_student, name="badge"),
    path("badge/verifie/<str:matricule>/", badge_views.badge_verify, name="badge_verify"),
]
