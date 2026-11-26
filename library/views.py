from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.views import teaching_staff_required

from .forms import BookForm, LoanForm
from .models import Book, Loan


@teaching_staff_required
def book_list(request):
    books = Book.objects.all()
    loans = Loan.objects.filter(returned_at__isnull=True)
    return render(request, "library/list.html", {"books": books, "active_loans": loans})


@teaching_staff_required
def book_create(request):
    form = BookForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Liv la ajoute.")
        return redirect("library:list")
    return render(request, "library/form.html", {"form": form, "titre": "Nouvo liv"})


@teaching_staff_required
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    form = BookForm(request.POST or None, instance=book)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Liv la mete ajou.")
        return redirect("library:list")
    return render(request, "library/form.html", {"form": form, "titre": "Modifye liv"})


@teaching_staff_required
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        book.delete()
        messages.success(request, "Liv la efase.")
        return redirect("library:list")
    return render(request, "library/confirm_delete.html", {"object": book})


@teaching_staff_required
def loan_create(request, book_pk=None):
    initial = {}
    if book_pk:
        initial["book"] = get_object_or_404(Book, pk=book_pk)
    form = LoanForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        loan = form.save(commit=False)
        loan.created_by = request.user
        loan.save()
        messages.success(request, "Emprunt la anrejistre.")
        return redirect("library:list")
    return render(request, "library/loan_form.html", {"form": form, "titre": "Nouvo emprunt"})


@teaching_staff_required
def loan_return(request, pk):
    loan = get_object_or_404(Loan, pk=pk, returned_at__isnull=True)
    if request.method == "POST":
        loan.returned_at = timezone.localdate()
        loan.save()
        messages.success(request, "Liv la retounen. Mèsi!")
    return redirect("library:list")
