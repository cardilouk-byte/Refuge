from django.urls import path

from . import views

app_name = "excel_manager"

urlpatterns = [
    path("excel/", views.index, name="index"),
    path("excel/eleves/export/", views.export_students, name="export_students"),
    path("excel/eleves/modele/", views.template_students, name="template_students"),
    path("excel/eleves/import/", views.import_students_view, name="import_students"),
    path("excel/notes/modele/", views.template_grades, name="template_grades"),
    path("excel/notes/export/", views.export_grades, name="export_grades"),
    path("excel/notes/import/", views.import_grades_view, name="import_grades"),
]
