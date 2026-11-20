from django.contrib import admin

from .models import Expense, FeeType, Invoice, Payment


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("label", "category", "amount", "spent_at", "created_by")
    list_filter = ("category",)
    search_fields = ("label", "note")


@admin.register(FeeType)
class FeeTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "school_year")
    list_filter = ("school_year",)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("receipt_number", "paid_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("student", "fee_type", "amount", "paid_amount_display", "status", "due_date")
    list_filter = ("status", "fee_type")
    search_fields = ("student__first_name", "student__last_name")
    inlines = [PaymentInline]

    @admin.display(description="Payé")
    def paid_amount_display(self, obj):
        return f"{obj.paid_amount} HTG"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "invoice", "amount", "method", "paid_at", "received_by")
    list_filter = ("method",)
    readonly_fields = ("receipt_number", "paid_at")
