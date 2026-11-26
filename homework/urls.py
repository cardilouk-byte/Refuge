from django.urls import path

from . import views

app_name = "homework"

urlpatterns = [
    path("", views.devoir_list, name="list"),
    path("nouveau/", views.devoir_create, name="create"),
    path("<int:pk>/modifier/", views.devoir_update, name="update"),
    path("<int:pk>/supprimer/", views.devoir_delete, name="delete"),
]
