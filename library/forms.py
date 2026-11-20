from django import forms

from students.models import Student

from .models import Book, Loan


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["title", "author", "isbn", "category", "description", "total_copies"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
            "isbn": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "total_copies": forms.NumberInput(attrs={"class": "form-control"}),
        }


class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ["book", "student", "due_date"]
        widgets = {
            "book": forms.Select(attrs={"class": "form-select"}),
            "student": forms.Select(attrs={"class": "form-select"}),
            "due_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }

    def clean(self):
        cleaned = super().clean()
        book = cleaned.get("book")
        if book and book.available_copies <= 0:
            raise forms.ValidationError("Pa gen egzemplar disponib pou liv sa a kounye a.")
        return cleaned
