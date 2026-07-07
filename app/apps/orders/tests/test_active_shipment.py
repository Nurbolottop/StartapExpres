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
