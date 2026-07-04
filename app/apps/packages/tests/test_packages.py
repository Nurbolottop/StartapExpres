import pytest
from django.urls import reverse

from apps.orders.choices import OrderStatus
from apps.orders.tests.factories import OrderFactory
from apps.packages.models import Package
from apps.packages.services import PackageService

pytestmark = pytest.mark.django_db

PACKAGES_URL = reverse('packages-list')
SCAN_URL = reverse('packages-scan')


def make_package(order=None, **kwargs) -> Package:
    order = order or OrderFactory()
    defaults = {'title': 'Коробка', 'weight': 5}
    defaults.update(kwargs)
    return Package.objects.create(order=order, **defaults)


class TestPackages:
    def test_operator_adds_package_to_order(self, auth_client, operator):
        order = OrderFactory()

        response = auth_client(operator).post(
            PACKAGES_URL,
            {'order': str(order.id), 'title': 'Документы', 'weight': '0.5'},
        )

        assert response.status_code == 201
        assert order.packages.count() == 1

    def test_volume_auto_calculated_from_dimensions(self, auth_client, operator):
        order = OrderFactory()

        response = auth_client(operator).post(
            PACKAGES_URL,
            {
                'order': str(order.id),
                'title': 'Куб',
                'weight': '1',
                'length': 100,
                'width': 100,
                'height': 100,
            },
        )

        assert response.status_code == 201
        assert response.json()['data']['volume'] == '1.000'

    def test_cannot_modify_after_shipping(self, auth_client, operator):
        order = OrderFactory(status=OrderStatus.IN_TRANSIT)
        package = make_package(order=order)

        response = auth_client(operator).patch(
            reverse('packages-detail', args=[package.id]), {'title': 'Новый'}
        )

        assert response.status_code == 409

    def test_client_sees_only_own_packages(self, auth_client, client_user):
        own_order = OrderFactory(client=client_user)
        make_package(order=own_order)
        make_package()  # чужой

        response = auth_client(client_user).get(PACKAGES_URL)

        assert response.json()['meta']['total'] == 1


class TestQR:
    def test_generate_qr_once(self, auth_client, warehouse_user):
        package = make_package()
        url = reverse('packages-generate-qr', args=[package.id])
        client = auth_client(warehouse_user)

        first = client.post(url)
        second = client.post(url)

        assert first.status_code == 200
        assert first.json()['data']['qr_code']
        assert second.status_code == 409
        assert second.json()['error']['code'] == 'PACKAGE_002'

    def test_scan_by_qr(self, auth_client, warehouse_user, superadmin):
        package = make_package()
        package = PackageService.generate_qr(actor=superadmin, package=package)

        response = auth_client(warehouse_user).post(SCAN_URL, {'qr_code': package.qr_code})

        assert response.status_code == 200
        assert response.json()['data']['id'] == str(package.id)
        assert package.order.tracking_events.filter(status='scanned').exists()

    def test_scan_unknown_qr_returns_404(self, auth_client, warehouse_user):
        response = auth_client(warehouse_user).post(SCAN_URL, {'qr_code': 'nope'})

        assert response.status_code == 404
        assert response.json()['error']['code'] == 'PACKAGE_001'

    def test_client_cannot_scan(self, auth_client, client_user):
        response = auth_client(client_user).post(SCAN_URL, {'qr_code': 'x'})

        assert response.status_code == 403
