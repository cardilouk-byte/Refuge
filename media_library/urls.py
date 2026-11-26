from django.urls import path

from . import views

app_name = "media_library"

urlpatterns = [
    path("medias/", views.index, name="index"),
    path("medias/televerser/", views.upload, name="upload"),
    path("medias/<int:pk>/supprimer/", views.delete, name="delete"),
]
