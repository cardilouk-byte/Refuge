from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("resultats/", views.results, name="results"),
    path(
        "connexion/",
        auth_views.LoginView.as_view(template_name="core/login.html"),
        name="login",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="logout"),
]
