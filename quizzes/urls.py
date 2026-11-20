from django.urls import path

from . import views

app_name = "quizzes"

urlpatterns = [
    path("", views.quiz_list, name="list"),
    path("nouveau/", views.quiz_create, name="create"),
    path("<int:pk>/modifier/", views.quiz_update, name="update"),
    path("<int:pk>/supprimer/", views.quiz_delete, name="delete"),
    path("<int:pk>/kesyon/", views.quiz_questions, name="questions"),
    path("<int:quiz_pk>/kesyon/<int:pk>/supprimer/", views.question_delete, name="question_delete"),
    path("<int:pk>/publie/", views.quiz_publish, name="publish"),
    path("<int:pk>/rezilta/", views.quiz_results, name="results"),
    path("<int:pk>/rezilta/excel/", views.quiz_excel, name="excel"),
    path("<int:pk>/fe/", views.quiz_take, name="take"),
]
