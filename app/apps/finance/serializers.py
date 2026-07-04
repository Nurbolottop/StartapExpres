from decimal import Decimal

from rest_framework import serializers

from apps.finance.choices import PaymentMethod, RefundReason
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


class PaymentSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id',
            'payment_number',
            'order',
            'order_number',
            'amount',
            'currency',
            'payment_method',
            'transaction_id',
            'paid_by',
            'paid_at',
            'status',
            'created_at',
        )
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Invoice
        fields = (
            'id',
            'invoice_number',
            'order',
            'order_number',
            'payment',
            'amount',
            'vat_percent',
            'issued_at',
            'due_date',
            'status',
            'created_at',
        )
        read_only_fields = fields


class RefundCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    reason = serializers.ChoiceField(choices=RefundReason.choices)
    comment = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ('id', 'payment', 'amount', 'reason', 'comment', 'created_by', 'created_at')
        read_only_fields = fields


class CashboxSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = Cashbox
        fields = ('id', 'branch', 'branch_name', 'balance', 'created_at', 'updated_at')
        read_only_fields = fields


class CashSessionSerializer(serializers.ModelSerializer):
    cashier_name = serializers.CharField(source='cashier.full_name', read_only=True)

    class Meta:
        model = CashSession
        fields = (
            'id',
            'cashbox',
            'cashier',
            'cashier_name',
            'opened_at',
            'closed_at',
            'opening_balance',
            'closing_balance',
        )
        read_only_fields = fields


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'cashbox', 'payment', 'amount', 'type', 'comment', 'created_by', 'created_at')
        read_only_fields = fields


class ExpenseSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    comment = serializers.CharField(max_length=255)


class DebtSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Debt
        fields = ('id', 'order', 'order_number', 'amount', 'paid_amount', 'due_date', 'status', 'created_at')
        read_only_fields = fields


class DebtPaySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))
    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices)


class FinancialReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialReport
        fields = ('id', 'period_type', 'period_date', 'data', 'created_at')
        read_only_fields = fields
