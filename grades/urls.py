from django.urls import path

from . import views

app_name = "grades"

urlpatterns = [
    path("", views.class_list, name="class_list"),
    path("klas/<int:classroom_pk>/", views.note_saisie, name="note_saisie"),
    path("lis-nor/", views.grade_admin_list, name="grade_list"),
    path("bulletin/", views.bulletin_home, name="bulletin_home"),
    path("bulletin/eleve/<int:student_pk>/", views.bulletin_student, name="bulletin_student"),
    path("bulletin/cik/<int:student_pk>/", views.bulletin_cycle, name="bulletin_cycle"),
    path("bulletin/klas/<int:classroom_pk>/", views.bulletin_class, name="bulletin_class"),
    path("bulletin/klas/<int:classroom_pk>/excel/", views.bulletin_excel, name="bulletin_excel"),
    path("tablo-done/", views.honour, name="honour"),
    path("carnet/model/", views.carnet_settings, name="carnet_settings"),
    path("carnet/eleve/<int:student_pk>/", views.carnet_print, name="carnet_print"),
    path("carnet/eleve/<int:student_pk>/pdf/", views.carnet_pdf, name="carnet_pdf"),
    path("carnet/klas/<int:classroom_pk>/pdf/", views.carnet_class_pdf, name="carnet_class_pdf"),
]
