from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.finance.choices import DebtStatus, PaymentStatus, TransactionType
from apps.finance.models import Cashbox, Debt, Invoice, Payment, Transaction
from apps.finance.services import ReportService, check_overdue_debts
from apps.orders.choices import OrderStatus, PaymentType
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db


def order_url(order_id, suffix: str = '') -> str:
    base = reverse('orders-detail', args=[order_id])
    return f'{base}{suffix}' if suffix else base


def paid_order(client_user, auth_client, operator, finance_user, total='1000'):
    order = OrderFactory(client=client_user, total_price=Decimal(total))
    auth_client(client_user).post(order_url(order.id, 'submit/'))
    auth_client(operator).post(order_url(order.id, 'confirm/'))
    auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': total})
    order.refresh_from_db()
    return order


class TestPaymentChain:
    def test_pay_creates_payment_transaction_invoice_and_cashbox(
        self, auth_client, client_user, operator, finance_user
    ):
        order = paid_order(client_user, auth_client, operator, finance_user)

        payment = Payment.objects.get(order=order)
        assert payment.payment_number.startswith('PAY-')
        assert payment.status == PaymentStatus.PAID
        assert Invoice.objects.filter(payment=payment).exists()
        transaction_row = Transaction.objects.get(payment=payment)
        assert transaction_row.type == TransactionType.INCOME
        cashbox = Cashbox.objects.get(branch=order.from_branch)
        assert cashbox.balance == Decimal('1000')
        assert order.status == OrderStatus.WAITING_RECEIVE

    def test_post_payment_creates_debt_and_unblocks_chain(
        self, auth_client, client_user, operator, finance_user
    ):
        order = OrderFactory(
            client=client_user, total_price=Decimal('500'), payment_type=PaymentType.POST_PAYMENT
        )
        auth_client(client_user).post(order_url(order.id, 'submit/'))
        auth_client(operator).post(order_url(order.id, 'confirm/'))

        response = auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '500'})
        order.refresh_from_db()
        debt = Debt.objects.get(order=order)

        assert response.status_code == 200
        assert order.status == OrderStatus.WAITING_RECEIVE
        assert debt.status == DebtStatus.OPEN
        assert debt.amount == Decimal('500')

    def test_completed_blocked_until_debt_closed(self, auth_client, client_user, operator, finance_user):
        order = OrderFactory(
            client=client_user, total_price=Decimal('500'), payment_type=PaymentType.POST_PAYMENT
        )
        auth_client(client_user).post(order_url(order.id, 'submit/'))
        auth_client(operator).post(order_url(order.id, 'confirm/'))
        auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '500'})
        from apps.orders.models import Order

        Order.objects.filter(id=order.id).update(status=OrderStatus.DELIVERED)
        order.refresh_from_db()

        blocked = auth_client(finance_user).post(order_url(order.id, 'status/'), {'status': 'completed'})
        assert blocked.status_code == 422
        assert blocked.json()['error']['code'] == 'PAYMENT_006'

        debt = Debt.objects.get(order=order)
        pay = auth_client(finance_user).post(
            reverse('debts-pay', args=[debt.id]), {'amount': '500', 'payment_method': 'cash'}
        )
        assert pay.status_code == 200

        done = auth_client(finance_user).post(order_url(order.id, 'status/'), {'status': 'completed'})
        assert done.status_code == 200

    def test_refund_creates_transaction_and_updates_status(
        self, auth_client, client_user, operator, finance_user
    ):
        order = paid_order(client_user, auth_client, operator, finance_user)
        payment = Payment.objects.get(order=order)

        response = auth_client(finance_user).post(
            reverse('payments-refund', args=[payment.id]),
            {'amount': '1000', 'reason': 'cancelled_order'},
        )
        payment.refresh_from_db()
        cashbox = Cashbox.objects.get(branch=order.from_branch)

        assert response.status_code == 201
        assert payment.status == PaymentStatus.REFUNDED
        assert cashbox.balance == Decimal('0')
        assert Transaction.objects.filter(payment=payment, type=TransactionType.REFUND).exists()

    def test_refund_cannot_exceed_payment(self, auth_client, client_user, operator, finance_user):
        order = paid_order(client_user, auth_client, operator, finance_user)
        payment = Payment.objects.get(order=order)

        response = auth_client(finance_user).post(
            reverse('payments-refund', args=[payment.id]),
            {'amount': '2000', 'reason': 'other'},
        )

        assert response.status_code == 422

    def test_operator_cannot_refund(self, auth_client, client_user, operator, finance_user):
        order = paid_order(client_user, auth_client, operator, finance_user)
        payment = Payment.objects.get(order=order)

        response = auth_client(operator).post(
            reverse('payments-refund', args=[payment.id]), {'amount': '100', 'reason': 'other'}
        )

        assert response.status_code == 403


class TestCashbox:
    def test_session_open_close_and_expense(self, auth_client, finance_user, client_user, operator):
        order = paid_order(client_user, auth_client, operator, finance_user)
        cashbox = Cashbox.objects.get(branch=order.from_branch)
        client = auth_client(finance_user)

        opened = client.post(reverse('cashboxes-open-session', args=[cashbox.id]))
        duplicate = client.post(reverse('cashboxes-open-session', args=[cashbox.id]))
        expense = client.post(
            reverse('cashboxes-expense', args=[cashbox.id]),
            {'amount': '200', 'comment': 'Топливо'},
        )
        closed = client.post(reverse('cashboxes-close-session', args=[cashbox.id]))

        assert opened.status_code == 201
        assert duplicate.status_code == 409
        assert expense.status_code == 201
        assert closed.status_code == 200
        cashbox.refresh_from_db()
        assert cashbox.balance == Decimal('800')
        assert closed.json()['data']['closing_balance'] == '800.00'


class TestDebtsAndReports:
    def test_overdue_debts_marked(self, superadmin, client_user):
        order = OrderFactory(client=client_user, payment_type=PaymentType.POST_PAYMENT)
        Debt.objects.create(
            order=order,
            amount=100,
            due_date=(timezone.now() - timedelta(days=1)).date(),
            created_by=superadmin,
        )

        count = check_overdue_debts()

        assert count == 1
        assert Debt.objects.first().status == DebtStatus.OVERDUE

    def test_daily_report_builds_metrics(self, auth_client, client_user, operator, finance_user):
        paid_order(client_user, auth_client, operator, finance_user)

        report = ReportService.build('daily', timezone.localdate())

        assert Decimal(report.data['income']) == Decimal('1000')
        assert report.data['payments_count'] == 1
        assert report.data['orders_count'] == 1

    def test_finance_reports_permission(self, auth_client, warehouse_user):
        response = auth_client(warehouse_user).get(reverse('financial-reports-list'))

        assert response.status_code == 403
