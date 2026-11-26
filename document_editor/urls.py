from django.urls import path

from . import views

app_name = "document_editor"

urlpatterns = [
    path("documents/", views.index, name="index"),
    path("documents/nouveau/", views.editor, name="create"),
    path("documents/<int:pk>/", views.editor, name="editor"),
    path("documents/<int:pk>/dupliquer/", views.duplicate, name="duplicate"),
    path("documents/<int:pk>/supprimer/", views.delete, name="delete"),
    path("documents/<int:pk>/export/docx/", views.export_docx, name="export_docx"),
    path("documents/<int:pk>/export/pdf/", views.export_pdf, name="export_pdf"),
    path("documents/<int:pk>/apercu/", views.preview, name="preview"),
]
