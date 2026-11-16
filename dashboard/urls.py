from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("tableau/", views.home, name="home"),
]
