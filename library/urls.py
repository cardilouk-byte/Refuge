from django.urls import path

from . import views

app_name = "library"

urlpatterns = [
    path("", views.book_list, name="list"),
    path("nouveau/", views.book_create, name="book_create"),
    path("<int:pk>/modifier/", views.book_update, name="book_update"),
    path("<int:pk>/supprimer/", views.book_delete, name="book_delete"),
    path("prets/nouveau/", views.loan_create, name="loan_create"),
    path("prets/<int:book_pk>/nouveau/", views.loan_create, name="loan_create_book"),
    path("prets/<int:pk>/retourne/", views.loan_return, name="loan_return"),
]
