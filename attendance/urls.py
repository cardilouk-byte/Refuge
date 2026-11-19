from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.home, name="home"),
    path("klas/<int:classroom_pk>/", views.take, name="take"),
    path("rapor/", views.report, name="report"),
]
