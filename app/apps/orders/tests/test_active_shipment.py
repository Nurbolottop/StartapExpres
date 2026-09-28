"""Тест поля active_shipment в детальном ответе заказа (доработка для
мобильного live-трекинга машины)."""

import pytest

from apps.orders.serializers import OrderSerializer
from apps.orders.tests.factories import OrderFactory
from apps.packages.models import Package
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment, ShipmentItem

pytestmark = pytest.mark.django_db


def _attach_shipment(order, status):
    shipment = Shipment.objects.create(
        shipment_number=f'SHP-TST-{status}',
        departure_branch=order.from_branch,
        arrival_branch=order.to_branch,
        status=status,
    )
    package = Package.objects.create(order=order, title='Груз', weight='1.000')
    ShipmentItem.objects.create(shipment=shipment, order=order, package=package)
    return shipment


class TestActiveShipment:
    def test_null_when_no_shipment(self):
        order = OrderFactory()
        assert OrderSerializer(order).data['active_shipment'] is None

    def test_returns_active_shipment(self):
        order = OrderFactory()
        shipment = _attach_shipment(order, ShipmentStatus.IN_TRANSIT)

        data = OrderSerializer(order).data['active_shipment']
        assert data is not None
        assert data['shipment_number'] == shipment.shipment_number
        assert data['status'] == ShipmentStatus.IN_TRANSIT

    def test_null_for_finished_shipment(self):
        order = OrderFactory()
        _attach_shipment(order, ShipmentStatus.COMPLETED)
        assert OrderSerializer(order).data['active_shipment'] is None


class TestLastCheckpoint:
    @staticmethod
    def _route_shipment(order):
        """Рейс в пути по маршруту из 3 точек, отмечены 1-я и 2-я."""
        import uuid

        from django.utils import timezone

        from apps.branches.tests.factories import CityFactory
        from apps.routes.models import Route, RoutePoint
        from apps.shipments.models import ShipmentCheckpoint

        suffix = uuid.uuid4().hex[:8]
        route = Route.objects.create(
            name='Бишкек — Ош',
            code=f'R-{suffix}',
            start_branch=order.from_branch,
            end_branch=order.to_branch,
            estimated_distance=672,
            estimated_duration=720,
        )
        points = [
            RoutePoint.objects.create(route=route, city=CityFactory(name=name), sequence=index)
            for index, name in enumerate(('Бишкек', 'Токтогул', 'Ош'), start=1)
        ]
        shipment = Shipment.objects.create(
            shipment_number=f'SHP-{suffix}',
            departure_branch=order.from_branch,
            arrival_branch=order.to_branch,
            route=route,
            status=ShipmentStatus.IN_TRANSIT,
        )
        package = Package.objects.create(order=order, title='Груз', weight='1.000')
        ShipmentItem.objects.create(shipment=shipment, order=order, package=package)
        now = timezone.now()
        for point, hours_ago in ((points[0], 3), (points[1], 1)):
            ShipmentCheckpoint.objects.create(
                shipment=shipment,
                route_point=point,
                client_id=uuid.uuid4(),
                reached_at=now - timezone.timedelta(hours=hours_ago),
            )
        return shipment

    def test_null_without_checkpoints(self):
        order = OrderFactory()
        _attach_shipment(order, ShipmentStatus.IN_TRANSIT)

        assert OrderSerializer(order).data['active_shipment']['last_checkpoint'] is None

    def test_latest_checkpoint_with_total_points(self):
        order = OrderFactory()
        self._route_shipment(order)

        last = OrderSerializer(order).data['active_shipment']['last_checkpoint']

        assert last['city_name'] == 'Токтогул'
        assert last['sequence'] == 2
        assert last['total_points'] == 3

    def test_list_does_not_query_per_order(self, django_assert_max_num_queries):
        from apps.orders.selectors import OrderSelector
        from apps.users.choices import Roles
        from apps.users.tests.factories import UserFactory

        user = UserFactory(role=Roles.SUPERADMIN)
        for _ in range(3):
            self._route_shipment(OrderFactory())

        with django_assert_max_num_queries(12):
            data = OrderSerializer(OrderSelector.for_user(user), many=True).data

        assert len(data) == 3
        assert all(item['active_shipment']['last_checkpoint'] for item in data)
