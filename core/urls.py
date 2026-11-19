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
    path("inscription/", views.signup, name="signup"),
    path("kalandriye/", views.calendar_view, name="calendar"),
    path("lavi-lekol/", views.school_life, name="school_life"),
    path("faq/", views.faq_page, name="faq"),
    path("kijan-enskri/", views.how_to_apply, name="how_to_apply"),
    path("apropo/", views.about_page, name="about_page"),
]
urlpatterns.append(path("telechaje/", views.download_page, name="download_page"))
urlpatterns.append(path("telechaje/aplikasyon/", views.download_app, name="download_app"))
