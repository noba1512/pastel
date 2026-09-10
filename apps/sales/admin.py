from django.contrib import admin

from apps.sales.models import CashSession, Payment, Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = (
        "product",
        "product_name_snapshot",
        "unit_price",
        "quantity",
        "subtotal",
    )


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("method", "amount", "amount_received", "change")


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ("number", "operator", "status", "opening_amount", "sales_total", "difference_cash", "opened_at")
    list_filter = ("status",)
    search_fields = ("number", "operator__username")
    readonly_fields = (
        "number",
        "operator",
        "status",
        "opening_amount",
        "opened_at",
        "closed_at",
        "closed_by",
        "sales_count",
        "canceled_count",
        "sales_total",
        "expected_cash",
        "expected_pix",
        "expected_debit",
        "expected_credit",
        "counted_cash",
        "counted_pix",
        "counted_debit",
        "counted_credit",
        "difference_cash",
        "difference_pix",
        "difference_debit",
        "difference_credit",
        "notes",
    )


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("number", "operator", "session", "status", "total", "finished_at")
    list_filter = ("status",)
    search_fields = ("number", "operator__username")
    inlines = [SaleItemInline, PaymentInline]
    readonly_fields = (
        "number",
        "operator",
        "session",
        "status",
        "subtotal",
        "discount",
        "total",
        "created_at",
        "finished_at",
        "canceled_at",
        "canceled_by",
        "cancel_reason",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("sale", "method", "amount", "amount_received", "change")
    list_filter = ("method",)
