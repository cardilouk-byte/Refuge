from django.urls import path

from . import views

app_name = "promotion"

urlpatterns = [
    path("", views.home, name="home"),
    path("nouvye/", views.new_year, name="new_year"),
    path("pasaj/", views.transition, name="transition"),
    path("pasaj/aplike/", views.apply, name="apply"),
    path("klas/<int:classroom_pk>/", views.detail, name="detail"),
]
