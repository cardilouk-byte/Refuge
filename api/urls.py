from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("", views.docs, name="docs"),
    path("ping/", views.ping, name="ping"),
    path("stats/", views.stats, name="stats"),
    path("nivo/", views.nivo, name="nivo"),
    path("matye/", views.matye, name="matye"),
    path("klas/", views.klas, name="klas"),
    path("elev/<str:matricule>/", views.elev, name="elev"),
    path("bulletin/<str:matricule>/", views.bulletin, name="bulletin"),
]
