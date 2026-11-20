from django.contrib import admin

from .models import Book, Loan


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "total_copies", "available_copies")
    list_filter = ("category",)


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("book", "student", "borrowed_at", "due_date", "returned_at", "is_late")
    list_filter = ("returned_at",)
