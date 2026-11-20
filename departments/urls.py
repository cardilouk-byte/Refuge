from django.urls import path

from . import views

app_name = "departments"

urlpatterns = [
    path("organigramme/", views.tree_view, name="tree"),
    path("organigramme/depatman/nouveau/", views.department_create, name="department_create"),
    path("organigramme/depatman/<int:pk>/", views.department_update, name="department_update"),
    path("organigramme/depatman/<int:pk>/supprimer/", views.department_delete, name="department_delete"),
    path("organigramme/post/nouveau/", views.position_create, name="position_create"),
    path("organigramme/post/<int:pk>/supprimer/", views.position_delete, name="position_delete"),
]
