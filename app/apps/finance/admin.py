from django.contrib import admin

from apps.finance.models import (
    Cashbox,
    CashSession,
    Debt,
    FinancialReport,
    Invoice,
    Payment,
    Refund,
    Transaction,
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'order', 'amount', 'payment_method', 'status', 'paid_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('payment_number', 'order__order_number', 'transaction_id')
    readonly_fields = [field.name for field in Payment._meta.fields]

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'order', 'amount', 'status', 'issued_at')
    list_filter = ('status',)
    search_fields = ('invoice_number', 'order__order_number')
    readonly_fields = [field.name for field in Invoice._meta.fields]


@admin.register(Cashbox)
class CashboxAdmin(admin.ModelAdmin):
    list_display = ('branch', 'balance')
    readonly_fields = ('id', 'balance', 'created_at', 'updated_at')


@admin.register(CashSession)
class CashSessionAdmin(admin.ModelAdmin):
    list_display = ('cashbox', 'cashier', 'opened_at', 'closed_at', 'opening_balance', 'closing_balance')
    readonly_fields = [field.name for field in CashSession._meta.fields]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('cashbox', 'type', 'amount', 'comment', 'created_at')
    list_filter = ('type',)
    readonly_fields = [field.name for field in Transaction._meta.fields]

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('payment', 'amount', 'reason', 'created_at')
    list_filter = ('reason',)
    readonly_fields = [field.name for field in Refund._meta.fields]


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'paid_amount', 'due_date', 'status')
    list_filter = ('status',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('period_type', 'period_date', 'created_at')
    list_filter = ('period_type',)
    readonly_fields = [field.name for field in FinancialReport._meta.fields]
