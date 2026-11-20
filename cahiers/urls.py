from django.urls import path

from . import views

app_name = "cahiers"

urlpatterns = [
    path("", views.index, name="index"),
    path("nouveau/", views.lesson_create, name="create"),
    path("<int:pk>/modifier/", views.lesson_update, name="update"),
    path("<int:pk>/supprimer/", views.lesson_delete, name="delete"),
    path("verifye/", views.verification, name="verification"),
    path("excel/", views.cahier_excel, name="excel"),
    path("verifye/<int:pk>/", views.verify, name="verify"),
]
