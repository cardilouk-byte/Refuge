from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from accounts.views import direction_required

from .forms import ExpenseForm, InvoiceForm, PaymentForm
from .models import Expense, FeeType, Invoice, Payment


def _finance_totals():
    revenue = Payment.objects.aggregate(t=Sum("amount"))["t"] or 0
    expenses = Expense.objects.aggregate(t=Sum("amount"))["t"] or 0
    invoices_total = Invoice.objects.aggregate(t=Sum("amount"))["t"] or 0
    unpaid = Invoice.objects.exclude(status=Invoice.Status.PAYE).aggregate(t=Sum("amount"))["t"] or 0
    return {
        "revenue": revenue,
        "expenses": expenses,
        "net": revenue - expenses,
        "unpaid": unpaid,
        "unpaid_count": Invoice.objects.exclude(status=Invoice.Status.PAYE).count(),
    }


@direction_required
def home(request):
    totals = _finance_totals()
    status_counts = {s[0]: 0 for s in Invoice.Status.choices}
    for st in Invoice.objects.all():
        status_counts[st.status] = status_counts.get(st.status, 0) + 1
    status_rows = []
    for code, label in Invoice.Status.choices:
        status_rows.append((code, label, status_counts.get(code, 0)))
    recent = Payment.objects.select_related("invoice__student", "invoice__fee_type")[:8]
    return render(
        request,
        "finance/home.html",
        {"totals": totals, "status_rows": status_rows, "recent": recent, "titre": "Finans lek\u00f2l la"},
    )


@direction_required
def invoice_list(request):
    statut = request.GET.get("statut", "")
    q = (request.GET.get("q") or "").strip()
    items = Invoice.objects.select_related("student", "fee_type")
    if statut:
        items = items.filter(status=statut)
    if q:
        items = items.filter(Q(student__first_name__icontains=q) | Q(student__last_name__icontains=q) | Q(student__matricule__icontains=q))
    items = items.order_by("-created_at")
    page_obj = Paginator(items, 50).get_page(request.GET.get("paj"))
    return render(
        request,
        "finance/invoice_list.html",
        {"page_obj": page_obj, "statut": statut, "q": q, "statuses": Invoice.Status.choices, "titre": "Fakti yo"},
    )


@direction_required
def invoice_create(request):
    form = InvoiceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        invoice = form.save(commit=False)
        invoice.save()
        messages.success(request, f"Fakti #{invoice.pk} kreye pou {invoice.student}.")
        return redirect("finance:invoice_list")
    return render(request, "finance/form.html", {"form": form, "titre": "Nouvo fakti", "back": "finance:invoice_list"})


@direction_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("student", "fee_type"), pk=pk)
    form = PaymentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        payment = form.save(commit=False)
        payment.invoice = invoice
        payment.received_by = request.user
        if payment.amount and payment.amount <= 0:
            form.add_error("amount", "Montan an dwe pi gran pase 0.")
        else:
            payment.save()
            invoice.update_status()
            messages.success(request, f"Peman {payment.receipt_number} anrejistre \u2014 {invoice.student}.")
            return redirect("finance:payment_receipt", pk=payment.pk)
    return render(
        request,
        "finance/invoice_detail.html",
        {"invoice": invoice, "form": form, "titre": f"Fakti #{invoice.pk}"},
    )


@direction_required
def payment_receipt(request, pk):
    payment = get_object_or_404(Payment.objects.select_related("invoice__student", "invoice__fee_type"), pk=pk)
    return render(request, "finance/receipt.html", {"payment": payment, "titre": f"Re\u00e7u {payment.receipt_number}"})


@direction_required
def expense_list(request):
    items = Expense.objects.all()[:100]
    form = ExpenseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        expense = form.save(commit=False)
        expense.created_by = request.user
        expense.save()
        messages.success(request, "Depans anrejistre.")
        return redirect("finance:expense_list")
    return render(request, "finance/expense_list.html", {"items": items, "form": form, "titre": "Depans yo"})


@direction_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == "POST":
        label = str(expense)
        expense.delete()
        messages.success(request, f"{label} efase.")
    return redirect("finance:expense_list")
