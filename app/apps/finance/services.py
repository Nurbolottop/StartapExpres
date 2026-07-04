"""Сервисный слой finance (ТЗ, раздел 11).

Единственный источник финансовых данных: оплата, возвраты, касса,
задолженности, отчёты. Все операции — в transaction.atomic с блокировками.
Цепочка оплаты: Payment → Transaction → Invoice → Audit(событие) → Notification.
"""

from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.common import events
from apps.common.services import generate_number
from apps.finance import exceptions
from apps.finance.choices import (
    DebtStatus,
    InvoiceStatus,
    PaymentMethod,
    PaymentStatus,
    RefundReason,
    TransactionType,
)
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
from apps.orders.choices import PaymentType
from apps.orders.models import Order

DEFAULT_DEBT_DAYS = 14


class PaymentService:
    @staticmethod
    def _cashbox_for_order(order: Order) -> Cashbox:
        cashbox, _ = Cashbox.objects.select_for_update().get_or_create(branch=order.from_branch)
        return cashbox

    @classmethod
    @transaction.atomic
    def register(
        cls, *, actor, order: Order, amount: Decimal, payment_method: str, transaction_id: str = ''
    ) -> Payment:
        """Приём оплаты: Payment → Transaction(income) → Invoice → события.

        Статусы заказа двигает OrderService.pay (FSM, частичная оплата).
        """
        from apps.orders.services import OrderService

        payment = Payment.objects.create(
            payment_number=generate_number('PAY'),
            order=order,
            amount=amount,
            payment_method=payment_method,
            transaction_id=transaction_id,
            paid_by=order.client,
            paid_at=timezone.now(),
            status=PaymentStatus.PAID,
            created_by=actor,
        )
        cashbox = cls._cashbox_for_order(order)
        cashbox.balance += amount
        cashbox.save(update_fields=['balance', 'updated_at'])
        Transaction.objects.create(
            cashbox=cashbox,
            payment=payment,
            amount=amount,
            type=TransactionType.INCOME,
            comment=f'Оплата {order.order_number}',
            created_by=actor,
        )
        invoice = InvoiceService.create_for_payment(actor=actor, payment=payment)

        OrderService.pay(actor=actor, order=order, amount=amount)

        events.publish(
            'payment.created',
            {
                'actor_id': str(actor.id),
                'model': 'Payment',
                'object_id': str(payment.id),
                'action': 'create_payment',
                'new': {
                    'amount': str(amount),
                    'method': payment_method,
                    'order': order.order_number,
                    'invoice': invoice.invoice_number,
                },
            },
            source='finance',
        )
        return payment

    @classmethod
    @transaction.atomic
    def register_post_payment(cls, *, actor, order: Order) -> Debt:
        """Постоплата (ТЗ, раздел 11): создаётся Debt, заказ идёт по цепочке."""
        from apps.orders.services import OrderService

        if order.payment_type != PaymentType.POST_PAYMENT:
            raise exceptions.OrderFinanceIncompleteException('Постоплата не разрешена для этого заказа.')
        debt, created = Debt.objects.get_or_create(
            order=order,
            defaults={
                'amount': order.total_price,
                'due_date': (timezone.now() + timedelta(days=DEFAULT_DEBT_DAYS)).date(),
                'created_by': actor,
            },
        )
        if created:
            OrderService.pay(actor=actor, order=order, amount=order.total_price)
            events.publish(
                'debt.created',
                {
                    'actor_id': str(actor.id),
                    'model': 'Debt',
                    'object_id': str(debt.id),
                    'action': 'create_debt',
                    'new': {'amount': str(debt.amount), 'due_date': str(debt.due_date)},
                },
                source='finance',
            )
        return debt

    @classmethod
    @transaction.atomic
    def pay_debt(cls, *, actor, debt: Debt, amount: Decimal, payment_method: str) -> Debt:
        debt = Debt.objects.select_for_update().get(id=debt.id)
        if debt.status == DebtStatus.CLOSED:
            raise exceptions.DebtClosedException()

        payment = Payment.objects.create(
            payment_number=generate_number('PAY'),
            order=debt.order,
            amount=amount,
            payment_method=payment_method,
            paid_by=debt.order.client,
            paid_at=timezone.now(),
            status=PaymentStatus.PAID,
            created_by=actor,
        )
        cashbox = cls._cashbox_for_order(debt.order)
        cashbox.balance += amount
        cashbox.save(update_fields=['balance', 'updated_at'])
        Transaction.objects.create(
            cashbox=cashbox,
            payment=payment,
            amount=amount,
            type=TransactionType.INCOME,
            comment=f'Погашение долга {debt.order.order_number}',
            created_by=actor,
        )

        debt.paid_amount += amount
        debt.status = DebtStatus.CLOSED if debt.paid_amount >= debt.amount else DebtStatus.PARTIALLY_PAID
        debt.updated_by = actor
        debt.save(update_fields=['paid_amount', 'status', 'updated_by', 'updated_at'])
        events.publish(
            'debt.paid',
            {
                'actor_id': str(actor.id),
                'model': 'Debt',
                'object_id': str(debt.id),
                'action': 'pay_debt',
                'new': {'paid_amount': str(debt.paid_amount), 'status': debt.status},
            },
            source='finance',
        )
        return debt

    @classmethod
    @transaction.atomic
    def refund(cls, *, actor, payment: Payment, amount: Decimal, reason: str, comment: str = '') -> Refund:
        """Возврат: отдельная транзакция, платёж не удаляется (ТЗ, разделы 11, 22)."""
        payment = Payment.objects.select_for_update().get(id=payment.id)
        if payment.status == PaymentStatus.REFUNDED:
            raise exceptions.PaymentAlreadyRefundedException()
        refunded = sum((r.amount for r in payment.refunds.all()), Decimal('0'))
        if refunded + amount > payment.amount:
            raise exceptions.RefundExceedsPaymentException()

        refund = Refund.objects.create(
            payment=payment, amount=amount, reason=reason, comment=comment, created_by=actor
        )
        cashbox = cls._cashbox_for_order(payment.order)
        cashbox.balance -= amount
        cashbox.save(update_fields=['balance', 'updated_at'])
        Transaction.objects.create(
            cashbox=cashbox,
            payment=payment,
            amount=-amount,
            type=TransactionType.REFUND,
            comment=f'Возврат: {reason}',
            created_by=actor,
        )
        if refunded + amount >= payment.amount:
            payment.status = PaymentStatus.REFUNDED
            payment.updated_by = actor
            payment.save(update_fields=['status', 'updated_by', 'updated_at'])
        events.publish(
            'payment.refunded',
            {
                'actor_id': str(actor.id),
                'model': 'Refund',
                'object_id': str(refund.id),
                'action': 'refund',
                'new': {'amount': str(amount), 'reason': reason},
            },
            source='finance',
        )
        return refund

    @staticmethod
    def is_order_settled(order: Order) -> bool:
        """Заказ финансово закрыт: PAID или Debt закрыт (ТЗ, раздел 11)."""
        if order.paid_amount >= order.total_price:
            debt = getattr(order, 'debt', None)
            if debt is not None and order.payment_type == PaymentType.POST_PAYMENT:
                return debt.status == DebtStatus.CLOSED
            return True
        return False


class InvoiceService:
    @staticmethod
    def create_for_payment(*, actor, payment: Payment) -> Invoice:
        return Invoice.objects.create(
            invoice_number=generate_number('INV'),
            order=payment.order,
            payment=payment,
            amount=payment.amount,
            issued_at=timezone.now(),
            status=InvoiceStatus.PAID,
            created_by=actor,
        )


class CashboxService:
    @staticmethod
    @transaction.atomic
    def open_session(*, actor, cashbox: Cashbox) -> CashSession:
        cashbox = Cashbox.objects.select_for_update().get(id=cashbox.id)
        if cashbox.sessions.filter(closed_at__isnull=True).exists():
            raise exceptions.CashboxSessionException('Смена уже открыта.')
        session = CashSession.objects.create(
            cashbox=cashbox, cashier=actor, opening_balance=cashbox.balance, created_by=actor
        )
        events.publish(
            'cashbox.session_opened',
            {
                'actor_id': str(actor.id),
                'model': 'CashSession',
                'object_id': str(session.id),
                'action': 'open_session',
                'new': {'opening_balance': str(session.opening_balance)},
            },
            source='finance',
        )
        return session

    @staticmethod
    @transaction.atomic
    def close_session(*, actor, cashbox: Cashbox) -> CashSession:
        cashbox = Cashbox.objects.select_for_update().get(id=cashbox.id)
        session = cashbox.sessions.filter(closed_at__isnull=True).first()
        if session is None:
            raise exceptions.CashboxSessionException('Нет открытой смены.')
        session.closed_at = timezone.now()
        session.closing_balance = cashbox.balance
        session.updated_by = actor
        session.save(update_fields=['closed_at', 'closing_balance', 'updated_by', 'updated_at'])
        events.publish(
            'cashbox.session_closed',
            {
                'actor_id': str(actor.id),
                'model': 'CashSession',
                'object_id': str(session.id),
                'action': 'close_session',
                'new': {'closing_balance': str(session.closing_balance)},
            },
            source='finance',
        )
        return session

    @staticmethod
    @transaction.atomic
    def add_expense(*, actor, cashbox: Cashbox, amount: Decimal, comment: str) -> Transaction:
        cashbox = Cashbox.objects.select_for_update().get(id=cashbox.id)
        cashbox.balance -= amount
        cashbox.save(update_fields=['balance', 'updated_at'])
        expense = Transaction.objects.create(
            cashbox=cashbox,
            amount=-amount,
            type=TransactionType.EXPENSE,
            comment=comment,
            created_by=actor,
        )
        events.publish(
            'cashbox.expense',
            {
                'actor_id': str(actor.id),
                'model': 'Transaction',
                'object_id': str(expense.id),
                'action': 'expense',
                'new': {'amount': str(amount), 'comment': comment},
            },
            source='finance',
        )
        return expense


class ReportService:
    @staticmethod
    def build(period_type: str, period_date) -> FinancialReport:
        """Показатели за период из фактических данных (ТЗ, разделы 11, 22)."""
        from django.db.models import Avg, Count, Sum

        if period_type == 'daily':
            payments = Payment.objects.filter(created_at__date=period_date)
            transactions = Transaction.objects.filter(created_at__date=period_date)
            orders = Order.objects.filter(created_at__date=period_date)
        else:
            payments = Payment.objects.filter(
                created_at__date__month=period_date.month, created_at__date__year=period_date.year
            )
            transactions = Transaction.objects.filter(
                created_at__date__month=period_date.month, created_at__date__year=period_date.year
            )
            orders = Order.objects.filter(
                created_at__date__month=period_date.month, created_at__date__year=period_date.year
            )

        income = transactions.filter(type=TransactionType.INCOME).aggregate(s=Sum('amount'))['s'] or 0
        expense = transactions.filter(type=TransactionType.EXPENSE).aggregate(s=Sum('amount'))['s'] or 0
        refunds = transactions.filter(type=TransactionType.REFUND).aggregate(s=Sum('amount'))['s'] or 0
        stats = payments.filter(status=PaymentStatus.PAID).aggregate(count=Count('id'), avg=Avg('amount'))
        open_debts = Debt.objects.exclude(status=DebtStatus.CLOSED).aggregate(s=Sum('amount'))['s'] or 0

        data = {
            'income': str(income),
            'expense': str(abs(expense)),
            'refunds': str(abs(refunds)),
            'profit': str(income + expense + refunds),
            'orders_count': orders.count(),
            'payments_count': stats['count'],
            'average_check': str(round(stats['avg'] or 0, 2)),
            'open_debts': str(open_debts),
        }
        report, _ = FinancialReport.objects.update_or_create(
            period_type=period_type, period_date=period_date, defaults={'data': data}
        )
        return report


def check_overdue_debts() -> int:
    """Просроченные долги → OVERDUE + событие (ТЗ, раздел 11)."""
    today = timezone.localdate()
    overdue = Debt.objects.filter(status__in=(DebtStatus.OPEN, DebtStatus.PARTIALLY_PAID), due_date__lt=today)
    count = 0
    for debt in overdue:
        debt.status = DebtStatus.OVERDUE
        debt.save(update_fields=['status', 'updated_at'])
        events.publish(
            'debt.overdue',
            {
                'actor_id': None,
                'model': 'Debt',
                'object_id': str(debt.id),
                'action': 'debt_overdue',
                'new': {'due_date': str(debt.due_date)},
            },
            source='finance',
        )
        count += 1
    return count


# Совместимость выбора метода оплаты заказа с методами платежа
ORDER_PAYMENT_METHOD_MAP = {
    PaymentType.CASH: PaymentMethod.CASH,
    PaymentType.CARD: PaymentMethod.CARD,
    PaymentType.QR: PaymentMethod.QR,
    PaymentType.BANK_TRANSFER: PaymentMethod.BANK_TRANSFER,
}


REFUND_REASONS = RefundReason
