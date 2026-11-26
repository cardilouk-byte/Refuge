from django.urls import path

from . import config_views, data_views, views

app_name = "dashboard"

urlpatterns = [
    path("tableau/", views.home, name="home"),
    path("tableau/done/", data_views.data_home, name="data_home"),
    path("tableau/done/<str:key>/", data_views.data_list, name="data_list"),
    path("tableau/done/<str:key>/nouvo/", data_views.data_create, name="data_create"),
    path("tableau/done/<str:key>/<int:pk>/modifye/", data_views.data_update, name="data_update"),
    path("tableau/done/<str:key>/<int:pk>/efase/", data_views.data_delete, name="data_delete"),
    path("tableau/done/pwofese/<int:pk>/kont/", data_views.teacher_account, name="teacher_account"),
    path("configuration/", config_views.config_home, name="config_home"),
    path("configuration/parametres/", config_views.config_settings, name="config_settings"),
    path("configuration/model-sit/", config_views.config_themes, name="config_themes"),
    path("configuration/model-sit/<str:key>/aplike/", config_views.config_theme_apply, name="config_theme_apply"),
    path("configuration/<slug:section>/", config_views.config_list, name="config_list"),
    path("configuration/<slug:section>/nouveau/", config_views.config_create, name="config_create"),
    path("configuration/<slug:section>/<int:pk>/", config_views.config_update, name="config_update"),
    path("configuration/<slug:section>/<int:pk>/supprimer/", config_views.config_delete, name="config_delete"),
]
