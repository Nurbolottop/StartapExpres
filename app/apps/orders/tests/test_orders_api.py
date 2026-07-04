import pytest
from django.urls import reverse

from apps.branches.tests.factories import BranchFactory
from apps.orders.choices import OrderStatus
from apps.orders.models import Order
from apps.orders.tests.factories import OrderFactory
from apps.tariffs.tests.factories import AdditionalServiceFactory, TariffFactory

pytestmark = pytest.mark.django_db

ORDERS_URL = reverse('orders-list')


def order_url(order_id, suffix: str = '') -> str:
    base = reverse('orders-detail', args=[order_id])
    return f'{base}{suffix}' if suffix else base


@pytest.fixture
def route():
    """Два филиала + тариф между их городами."""
    from_branch, to_branch = BranchFactory(), BranchFactory()
    tariff = TariffFactory(
        from_city=from_branch.city,
        to_city=to_branch.city,
        base_price=200,
        price_per_kg=50,
        price_per_m3=0,
        insurance_percent=1,
    )
    return from_branch, to_branch, tariff


def order_payload(from_branch, to_branch, **extra) -> dict:
    payload = {
        'sender_name': 'Асан',
        'sender_phone': '+996700111111',
        'receiver_name': 'Болот',
        'receiver_phone': '+996700222222',
        'from_branch': str(from_branch.id),
        'to_branch': str(to_branch.id),
        'packages': [{'title': 'Коробка', 'weight': '10', 'declared_price': '5000'}],
    }
    payload.update(extra)
    return payload


class TestOrderCreate:
    def test_client_creates_own_order_with_price(self, auth_client, client_user, route):
        from_branch, to_branch, _ = route

        response = auth_client(client_user).post(
            ORDERS_URL, order_payload(from_branch, to_branch), format='json'
        )
        body = response.json()

        assert response.status_code == 201
        assert body['data']['order_number'].startswith('ORD-')
        assert body['data']['status'] == OrderStatus.DRAFT
        # 200 + 10*50 + 5000*1% = 750
        assert body['data']['total_price'] == '750.00'
        assert body['data']['client'] == str(client_user.id)
        assert len(body['data']['packages']) == 1

    def test_operator_creates_order_for_client(self, auth_client, operator, client_user, route):
        from_branch, to_branch, _ = route

        response = auth_client(operator).post(
            ORDERS_URL,
            order_payload(from_branch, to_branch, client=str(client_user.id)),
            format='json',
        )

        assert response.status_code == 201
        assert response.json()['data']['client'] == str(client_user.id)

    def test_order_with_services_included_in_price(self, auth_client, client_user, route):
        from_branch, to_branch, _ = route
        service = AdditionalServiceFactory(price=300)

        response = auth_client(client_user).post(
            ORDERS_URL,
            order_payload(from_branch, to_branch, services=[str(service.id)]),
            format='json',
        )
        body = response.json()

        assert response.status_code == 201
        assert body['data']['total_price'] == '1050.00'
        assert body['data']['services'][0]['price'] == '300.00'

    def test_order_without_packages_rejected(self, auth_client, client_user, route):
        from_branch, to_branch, _ = route
        payload = order_payload(from_branch, to_branch, packages=[])

        response = auth_client(client_user).post(ORDERS_URL, payload, format='json')

        assert response.status_code == 400

    def test_warehouse_cannot_create_order(self, auth_client, warehouse_user, route):
        from_branch, to_branch, _ = route

        response = auth_client(warehouse_user).post(
            ORDERS_URL, order_payload(from_branch, to_branch), format='json'
        )

        assert response.status_code == 403

    def test_idempotency_key_prevents_duplicate(self, auth_client, client_user, route):
        from_branch, to_branch, _ = route
        client = auth_client(client_user)
        payload = order_payload(from_branch, to_branch)

        first = client.post(ORDERS_URL, payload, format='json', HTTP_IDEMPOTENCY_KEY='k-1')
        second = client.post(ORDERS_URL, payload, format='json', HTTP_IDEMPOTENCY_KEY='k-1')

        assert first.status_code == second.status_code == 201
        assert first.json()['data']['id'] == second.json()['data']['id']
        assert Order.objects.count() == 1


class TestOrderScoping:
    def test_client_sees_only_own_orders(self, auth_client, client_user):
        OrderFactory(client=client_user)
        OrderFactory()  # чужой заказ

        response = auth_client(client_user).get(ORDERS_URL)
        body = response.json()

        assert body['meta']['total'] == 1

    def test_client_cannot_open_foreign_order(self, auth_client, client_user):
        foreign = OrderFactory()

        response = auth_client(client_user).get(order_url(foreign.id))

        assert response.status_code == 404

    def test_operator_sees_all_orders(self, auth_client, operator, client_user):
        OrderFactory(client=client_user)
        OrderFactory()

        response = auth_client(operator).get(ORDERS_URL)

        assert response.json()['meta']['total'] == 2


class TestOrderFlow:
    def test_full_happy_path_to_completed(
        self, auth_client, client_user, operator, warehouse_user, finance_user
    ):
        order = OrderFactory(client=client_user, total_price=1000)

        client = auth_client(client_user)
        assert client.post(order_url(order.id, 'submit/')).status_code == 200
        assert auth_client(operator).post(order_url(order.id, 'confirm/')).status_code == 200

        pay = auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '1000'})
        assert pay.status_code == 200
        assert pay.json()['data']['status'] == OrderStatus.WAITING_RECEIVE

        wh_client = auth_client(warehouse_user)
        for target in ['received', 'in_warehouse', 'waiting_shipment', 'loaded']:
            response = wh_client.post(order_url(order.id, 'status/'), {'status': target})
            assert response.status_code == 200, response.json()

        assert wh_client.post(order_url(order.id, 'status/'), {'status': 'in_transit'}).status_code == 200
        assert wh_client.post(order_url(order.id, 'status/'), {'status': 'arrived'}).status_code == 200

        for target in ['ready_for_pickup', 'delivered']:
            assert wh_client.post(order_url(order.id, 'status/'), {'status': target}).status_code == 200
        done = auth_client(finance_user).post(order_url(order.id, 'status/'), {'status': 'completed'})
        assert done.status_code == 200

        order.refresh_from_db()
        assert order.status == OrderStatus.COMPLETED
        # submit(1) + confirm(2) + pay(2) + склад(4) + водитель(2) + выдача(2) + завершение(1)
        assert order.status_history.count() == 14

    def test_invalid_transition_rejected(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.DRAFT)

        response = auth_client(operator).post(order_url(order.id, 'status/'), {'status': 'delivered'})

        assert response.status_code == 409
        assert response.json()['error']['code'] == 'ORDER_004'

    def test_role_cannot_perform_foreign_transition(self, auth_client, warehouse_user):
        order = OrderFactory(status=OrderStatus.WAITING_CONFIRMATION)

        response = auth_client(warehouse_user).post(order_url(order.id, 'status/'), {'status': 'confirmed'})

        assert response.status_code == 403

    def test_version_conflict_returns_409(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.DRAFT)

        response = auth_client(operator).post(
            order_url(order.id, 'status/'),
            {'status': 'waiting_confirmation', 'version': 99},
        )

        assert response.status_code == 409

    def test_partial_payment_blocks_full_status(self, auth_client, finance_user, operator, client_user):
        order = OrderFactory(client=client_user, total_price=1000)
        auth_client(client_user).post(order_url(order.id, 'submit/'))
        auth_client(operator).post(order_url(order.id, 'confirm/'))

        partial = auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '400'})
        order.refresh_from_db()

        assert partial.status_code == 200
        assert order.status == OrderStatus.PARTIALLY_PAID
        assert order.paid_amount == 400

        full = auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '600'})
        order.refresh_from_db()
        assert full.status_code == 200
        assert order.status == OrderStatus.WAITING_RECEIVE

    def test_pay_already_paid_rejected(self, auth_client, finance_user, operator, client_user):
        order = OrderFactory(client=client_user, total_price=100)
        auth_client(client_user).post(order_url(order.id, 'submit/'))
        auth_client(operator).post(order_url(order.id, 'confirm/'))
        auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '100'})

        response = auth_client(finance_user).post(order_url(order.id, 'pay/'), {'amount': '1'})

        assert response.status_code == 409
        assert response.json()['error']['code'] == 'ORDER_002'


class TestOrderRules:
    def test_client_cancels_before_confirmation(self, auth_client, client_user):
        order = OrderFactory(client=client_user, status=OrderStatus.WAITING_CONFIRMATION)

        response = auth_client(client_user).post(order_url(order.id, 'cancel/'))

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.CANCELLED

    def test_client_cannot_cancel_after_confirmation(self, auth_client, client_user):
        order = OrderFactory(client=client_user, status=OrderStatus.WAITING_PAYMENT)

        response = auth_client(client_user).post(order_url(order.id, 'cancel/'))

        assert response.status_code == 403

    def test_operator_cancels_after_confirmation(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.WAITING_PAYMENT)

        response = auth_client(operator).post(order_url(order.id, 'cancel/'), {'comment': 'отказ'})

        assert response.status_code == 200

    def test_frozen_fields_after_confirmation(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.WAITING_PAYMENT)

        response = auth_client(operator).patch(order_url(order.id), {'receiver_name': 'Другой'})

        assert response.status_code == 409
        assert response.json()['error']['code'] == 'ORDER_007'

    def test_comment_editable_after_confirmation(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.WAITING_PAYMENT)

        response = auth_client(operator).patch(order_url(order.id), {'comment': 'позвонить'})

        assert response.status_code == 200

    def test_no_edits_after_shipping(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.IN_TRANSIT)

        response = auth_client(operator).patch(order_url(order.id), {'comment': 'x'})

        assert response.status_code == 409

    def test_need_correction_flow(self, auth_client, operator, client_user):
        order = OrderFactory(client=client_user, status=OrderStatus.WAITING_CONFIRMATION)

        response = auth_client(operator).post(
            order_url(order.id, 'need-correction/'), {'comment': 'неверный телефон'}
        )

        assert response.status_code == 200
        order.refresh_from_db()
        assert order.status == OrderStatus.NEED_CORRECTION

    def test_history_and_tracking_endpoints(self, auth_client, client_user, operator):
        order = OrderFactory(client=client_user)
        auth_client(client_user).post(order_url(order.id, 'submit/'))
        auth_client(operator).post(order_url(order.id, 'confirm/'))

        history = auth_client(client_user).get(order_url(order.id, 'history/')).json()
        tracking = auth_client(client_user).get(order_url(order.id, 'tracking/')).json()

        assert [item['to_status'] for item in history['data']] == [
            'waiting_confirmation',
            'confirmed',
            'waiting_payment',
        ]
        assert len(tracking['data']) == 3
