import pytest
from django.urls import reverse

from apps.notifications.choices import NotificationStatus, NotificationType
from apps.notifications.models import Notification, NotificationTemplate
from apps.notifications.services import render_template
from apps.orders.tests.factories import OrderFactory

pytestmark = pytest.mark.django_db

NOTIFICATIONS_URL = reverse('notifications-list')


class TestTemplates:
    def test_render_substitutes_variables(self):
        assert render_template('Заказ {{order}} на {{price}}', {'order': 'ORD-1', 'price': 100}) == (
            'Заказ ORD-1 на 100'
        )

    def test_seeded_templates_exist(self):
        assert NotificationTemplate.objects.filter(name='order.created').exists()
        assert NotificationTemplate.objects.count() >= 10


class TestEventDrivenNotifications:
    def test_order_creation_notifies_client(
        self, auth_client, client_user, operator, django_capture_on_commit_callbacks
    ):
        from apps.branches.tests.factories import BranchFactory
        from apps.tariffs.tests.factories import TariffFactory

        from_branch, to_branch = BranchFactory(), BranchFactory()
        TariffFactory(from_city=from_branch.city, to_city=to_branch.city)

        with django_capture_on_commit_callbacks(execute=True):
            auth_client(client_user).post(
                reverse('orders-list'),
                {
                    'sender_name': 'А',
                    'sender_phone': '+996700111111',
                    'receiver_name': 'Б',
                    'receiver_phone': '+996700222222',
                    'from_branch': str(from_branch.id),
                    'to_branch': str(to_branch.id),
                    'packages': [{'title': 'Коробка', 'weight': '1'}],
                },
                format='json',
            )

        notification = Notification.objects.filter(user=client_user, event_type='order.created').first()
        assert notification is not None
        assert 'ORD-' in notification.body
        # celery eager: доставка in_app выполнена сразу
        notification.refresh_from_db()
        assert notification.status == NotificationStatus.DELIVERED

    def test_confirm_notifies_client(self, auth_client, client_user, operator):
        order = OrderFactory(client=client_user)
        auth_client(client_user).post(reverse('orders-detail', args=[order.id]) + 'submit/')
        auth_client(operator).post(reverse('orders-detail', args=[order.id]) + 'confirm/')

        assert Notification.objects.filter(user=client_user, event_type='order.confirmed').exists()


class TestNotificationAPI:
    def test_user_sees_only_own_notifications(self, auth_client, client_user, operator):
        Notification.objects.create(user=client_user, title='A', body='B')
        Notification.objects.create(user=operator, title='X', body='Y')

        response = auth_client(client_user).get(NOTIFICATIONS_URL)

        assert response.json()['meta']['total'] == 1

    def test_mark_read(self, auth_client, client_user):
        notification = Notification.objects.create(user=client_user, title='A', body='B')

        response = auth_client(client_user).patch(reverse('notifications-read', args=[notification.id]))

        assert response.status_code == 200
        notification.refresh_from_db()
        assert notification.is_read is True

    def test_operator_sends_manual_notification(self, auth_client, operator, client_user):
        response = auth_client(operator).post(
            reverse('notifications-send'),
            {'user': str(client_user.id), 'title': 'Внимание', 'body': 'Заберите груз'},
        )

        assert response.status_code == 201
        assert Notification.objects.filter(user=client_user, title='Внимание').exists()

    def test_client_cannot_send(self, auth_client, client_user):
        response = auth_client(client_user).post(
            reverse('notifications-send'),
            {'user': str(client_user.id), 'title': 'x', 'body': 'y'},
        )

        assert response.status_code == 403

    def test_templates_managed_by_director(self, auth_client, director, operator):
        create = auth_client(director).post(
            reverse('notification-templates-list'),
            {
                'name': 'order.cancelled',
                'type': NotificationType.IN_APP,
                'language': 'ru',
                'title': 'Заказ отменён',
                'body': 'Заказ {{order}} отменён.',
            },
        )
        forbidden = auth_client(operator).get(reverse('notification-templates-list'))

        assert create.status_code == 201
        assert forbidden.status_code == 403


class TestDashboards:
    def test_each_role_gets_own_dashboard(
        self, auth_client, superadmin, operator, warehouse_user, driver, client_user, finance_user
    ):
        url = reverse('dashboard')

        management = auth_client(superadmin).get(url).json()['data']
        ops = auth_client(operator).get(url).json()['data']
        warehouse = auth_client(warehouse_user).get(url).json()['data']
        drv = auth_client(driver).get(url).json()['data']
        client_data = auth_client(client_user).get(url).json()['data']
        finance = auth_client(finance_user).get(url).json()['data']

        assert 'users_total' in management
        assert 'new_orders' in ops
        assert 'cells_total' in warehouse
        assert 'my_active_shipments' in drv
        assert 'my_orders' in client_data
        assert 'income' in finance

    def test_reports_forbidden_for_operator(self, auth_client, operator):
        response = auth_client(operator).get(reverse('reports-finance'))

        assert response.status_code == 403

    def test_orders_report_for_director(self, auth_client, director, client_user):
        OrderFactory(client=client_user)

        response = auth_client(director).get(reverse('reports-orders'))
        body = response.json()

        assert response.status_code == 200
        assert body['data']['created'] == 1
