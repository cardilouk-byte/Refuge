from django.urls import path

from . import views

app_name = "portals"

urlpatterns = [
    path("portail/professeur/", views.professeur, name="professeur"),
    path("portail/eleve/", views.eleve, name="eleve"),
    path("portail/parent/", views.parent_home, name="parent"),
    path("portail/parent/enfant/<int:pk>/", views.child_detail, name="child_detail"),
]
