from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.common.idempotency import idempotent
from apps.common.permissions import ActionPermissionsMixin
from apps.finance import permissions as finance_permissions
from apps.finance.models import Cashbox, Debt, FinancialReport, Invoice, Payment, Transaction
from apps.finance.serializers import (
    CashboxSerializer,
    CashSessionSerializer,
    DebtPaySerializer,
    DebtSerializer,
    ExpenseSerializer,
    FinancialReportSerializer,
    InvoiceSerializer,
    PaymentSerializer,
    RefundCreateSerializer,
    RefundSerializer,
    TransactionSerializer,
)
from apps.finance.services import CashboxService, PaymentService


@extend_schema(tags=['finance'])
class PaymentViewSet(ActionPermissionsMixin, ReadOnlyModelViewSet):
    """Платежи: создаются через POST /orders/{id}/pay; удаление запрещено."""

    serializer_class = PaymentSerializer
    filterset_fields = ('status', 'payment_method', 'order')
    search_fields = ('payment_number', 'transaction_id', 'order__order_number')
    ordering_fields = ('created_at', 'amount')

    permission_classes_by_action = {
        '__default__': (finance_permissions.CanViewFinance,),
        'refund': (finance_permissions.CanRefund,),
    }

    def get_queryset(self):
        return Payment.objects.select_related('order', 'paid_by')

    @extend_schema(
        request=RefundCreateSerializer, responses={201: RefundSerializer}, summary='Возврат платежа'
    )
    @idempotent
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = PaymentService.refund(
            actor=request.user, payment=self.get_object(), **serializer.validated_data
        )
        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['finance'])
class InvoiceViewSet(ReadOnlyModelViewSet):
    serializer_class = InvoiceSerializer
    permission_classes = (finance_permissions.CanViewFinance,)
    filterset_fields = ('status', 'order')
    search_fields = ('invoice_number', 'order__order_number')
    ordering_fields = ('created_at', 'amount')

    def get_queryset(self):
        return Invoice.objects.select_related('order', 'payment')


@extend_schema(tags=['finance'])
class CashboxViewSet(ActionPermissionsMixin, ReadOnlyModelViewSet):
    serializer_class = CashboxSerializer
    filterset_fields = ('branch',)

    permission_classes_by_action = {
        '__default__': (finance_permissions.CanViewFinance,),
        'open_session': (finance_permissions.CanManageFinance,),
        'close_session': (finance_permissions.CanManageFinance,),
        'expense': (finance_permissions.CanManageFinance,),
        'transactions': (finance_permissions.CanViewFinance,),
    }

    def get_queryset(self):
        return Cashbox.objects.select_related('branch')

    @extend_schema(request=None, responses={201: CashSessionSerializer}, summary='Открыть смену')
    @action(detail=True, methods=['post'], url_path='open-session')
    def open_session(self, request, pk=None):
        session = CashboxService.open_session(actor=request.user, cashbox=self.get_object())
        return Response(CashSessionSerializer(session).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=CashSessionSerializer, summary='Закрыть смену')
    @action(detail=True, methods=['post'], url_path='close-session')
    def close_session(self, request, pk=None):
        session = CashboxService.close_session(actor=request.user, cashbox=self.get_object())
        return Response(CashSessionSerializer(session).data)

    @extend_schema(
        request=ExpenseSerializer, responses={201: TransactionSerializer}, summary='Расход из кассы'
    )
    @action(detail=True, methods=['post'])
    def expense(self, request, pk=None):
        serializer = ExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        expense = CashboxService.add_expense(
            actor=request.user, cashbox=self.get_object(), **serializer.validated_data
        )
        return Response(TransactionSerializer(expense).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=TransactionSerializer(many=True), summary='Транзакции кассы')
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        from apps.common.pagination import DefaultPageNumberPagination

        queryset = Transaction.objects.filter(cashbox=self.get_object())
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(TransactionSerializer(page, many=True).data)


@extend_schema(tags=['finance'])
class DebtViewSet(ActionPermissionsMixin, ReadOnlyModelViewSet):
    serializer_class = DebtSerializer
    filterset_fields = ('status',)
    search_fields = ('order__order_number',)
    ordering_fields = ('due_date', 'amount')

    permission_classes_by_action = {
        '__default__': (finance_permissions.CanViewFinance,),
        'pay': (finance_permissions.CanManageFinance,),
    }

    def get_queryset(self):
        return Debt.objects.select_related('order')

    @extend_schema(request=DebtPaySerializer, responses=DebtSerializer, summary='Погасить долг')
    @idempotent
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        serializer = DebtPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        debt = PaymentService.pay_debt(
            actor=request.user, debt=self.get_object(), **serializer.validated_data
        )
        return Response(DebtSerializer(debt).data)


@extend_schema(tags=['finance'])
class FinancialReportViewSet(ReadOnlyModelViewSet):
    serializer_class = FinancialReportSerializer
    permission_classes = (finance_permissions.CanManageFinance,)
    filterset_fields = ('period_type', 'period_date')
    ordering_fields = ('period_date',)

    def get_queryset(self):
        return FinancialReport.objects.all()
