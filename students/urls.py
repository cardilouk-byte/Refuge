from django.urls import path

from . import badge_views, views

app_name = "students"

urlpatterns = [
    path("eleve/", views.student_list, name="student_list"),
    path("eleve/nouveau/", views.student_create, name="student_create"),
    path("eleve/<int:pk>/modifier/", views.student_update, name="student_update"),
    path("eleve/<int:pk>/kont/", views.student_account, name="student_account"),
    path("badge/", badge_views.badge_own, name="badge_own"),
    path("eleves/<int:pk>/badge/", badge_views.badge_student, name="badge"),
    path("badge/verifie/<str:matricule>/", badge_views.badge_verify, name="badge_verify"),
]
