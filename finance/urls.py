from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.home, name="home"),
    path("fakti/", views.invoice_list, name="invoice_list"),
    path("fakti/nouvo/", views.invoice_create, name="invoice_create"),
    path("fakti/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("resi/<int:pk>/", views.payment_receipt, name="payment_receipt"),
    path("depans/", views.expense_list, name="expense_list"),
    path("depans/<int:pk>/efase/", views.expense_delete, name="expense_delete"),
]
