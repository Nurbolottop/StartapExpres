"""seed_demo: полный демо-стенд для мобильного приложения, повторный запуск без дублей."""

from io import StringIO

import pytest
from django.core.management import call_command

from apps.orders.choices import OrderStatus
from apps.orders.models import Order
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment, ShipmentCheckpoint
from apps.tracking.models import TrackingEvent
from apps.users.models import User

pytestmark = pytest.mark.django_db


def seed() -> str:
    out = StringIO()
    call_command('seed_demo', stdout=out)
    return out.getvalue()


def test_seed_demo_builds_full_stand_and_is_idempotent():
    output = seed()
    counts = (Order.objects.count(), Shipment.objects.count(), ShipmentCheckpoint.objects.count())

    second = seed()

    assert (Order.objects.count(), Shipment.objects.count(), ShipmentCheckpoint.objects.count()) == counts
    assert 'уже есть, пропуск' in second
    assert 'QR-коды грузов' in output

    client_orders = Order.objects.filter(client__phone='+996700900777')
    client_statuses = set(client_orders.values_list('status', flat=True))
    assert {
        OrderStatus.WAITING_RECEIVE,
        OrderStatus.IN_WAREHOUSE,
        OrderStatus.IN_TRANSIT,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.DRAFT,
        OrderStatus.DAMAGED,
    } <= client_statuses

    statuses = set(Shipment.objects.values_list('status', flat=True))
    assert {
        ShipmentStatus.READY,
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.ARRIVED,
        ShipmentStatus.COMPLETED,
    } <= statuses

    in_transit = Shipment.objects.get(status=ShipmentStatus.IN_TRANSIT)
    assert in_transit.driver.phone == '+996700900005'
    assert in_transit.route is not None
    assert in_transit.checkpoints.count() == 2

    transit_order = Order.objects.get(status=OrderStatus.IN_TRANSIT)
    assert TrackingEvent.objects.filter(order=transit_order, status='checkpoint_reached').count() == 2

    warehouse = User.objects.get(phone='+996700900004')
    assert warehouse.employee_profile.branch.name == 'Бишкек — центральный'
    osh_warehouse = User.objects.get(phone='+996700900009')
    assert osh_warehouse.employee_profile.branch.code == 'OSH01'
