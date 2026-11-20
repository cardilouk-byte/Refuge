from django.urls import path

from .views import role_home

app_name = "accounts"

urlpatterns = [
    path("apres-connexion/", role_home, name="role_home"),
]
