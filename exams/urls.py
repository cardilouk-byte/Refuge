from django.urls import path

from . import views

app_name = "exams"

urlpatterns = [
    path("", views.exam_list, name="list"),
    path("nouveau/", views.exam_create, name="create"),
    path("<int:pk>/modifier/", views.exam_update, name="update"),
    path("<int:pk>/supprimer/", views.exam_delete, name="delete"),
]
