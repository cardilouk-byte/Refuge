from django.urls import path

from . import views

app_name = "preregistration"

urlpatterns = [
    path("preinscription/", views.start, name="start"),
    path("preinscription/etap/<int:num>/", views.step, name="step"),
    path("preinscription/rezime/", views.review, name="review"),
    path("preinscriptions/", views.admin_list, name="admin_list"),
    path("preinscriptions/<int:pk>/", views.admin_detail, name="admin_detail"),
    path("preinscriptions/<int:pk>/estatut/", views.set_status, name="set_status"),
    path("preinscriptions/<int:pk>/konveti/", views.convert, name="convert"),
]
