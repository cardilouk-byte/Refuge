from django.urls import path

from . import config_views, views

app_name = "dashboard"

urlpatterns = [
    path("tableau/", views.home, name="home"),
    path("configuration/", config_views.config_home, name="config_home"),
    path("configuration/parametres/", config_views.config_settings, name="config_settings"),
    path("configuration/model-sit/", config_views.config_themes, name="config_themes"),
    path("configuration/model-sit/<str:key>/aplike/", config_views.config_theme_apply, name="config_theme_apply"),
    path("configuration/<slug:section>/", config_views.config_list, name="config_list"),
    path("configuration/<slug:section>/nouveau/", config_views.config_create, name="config_create"),
    path("configuration/<slug:section>/<int:pk>/", config_views.config_update, name="config_update"),
    path("configuration/<slug:section>/<int:pk>/supprimer/", config_views.config_delete, name="config_delete"),
]
