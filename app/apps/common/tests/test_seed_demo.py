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


def test_reset_scenarios_restores_stand_after_reviewer():
    """Ревьюер «расходует» сценарии; --reset-scenarios возвращает исходное состояние."""
    from decimal import Decimal

    from apps.branches.models import Branch
    from apps.common.management.commands.seed_demo import PAID_CHAIN, Command, _box
    from apps.finance.choices import PaymentMethod
    from apps.finance.models import Cashbox
    from apps.finance.services import PaymentService
    from apps.orders.transitions import OrderTransitionService
    from apps.shipments.models import Incident
    from apps.vehicles.choices import VehicleStatus
    from apps.vehicles.models import Vehicle
    from apps.warehouses.models import WarehouseCell

    seed()

    def snapshot():
        return {
            'orders': sorted(Order.objects.values_list('status', flat=True)),
            'shipments': sorted(Shipment.objects.values_list('status', flat=True)),
            'checkpoints': ShipmentCheckpoint.objects.count(),
            'cells': sorted(WarehouseCell.objects.values_list('code', 'occupied_weight', 'occupied_volume')),
            'cash': sorted(Cashbox.objects.exclude(balance=0).values_list('branch__code', 'balance')),
            'busy': Vehicle.objects.filter(status=VehicleStatus.BUSY).count(),
        }

    initial = snapshot()
    client = User.objects.get(phone='+996700900777')
    admin = User.objects.get(phone='+996700900001')

    draft = Order.objects.get(client=client, status=OrderStatus.DRAFT)
    OrderTransitionService.change(order=draft, to_status=OrderStatus.CANCELLED, actor=client)
    # свой заказ ревьюера — без маркера сценария, ловится по демо-клиенту
    ctx = {'actor': admin, 'branches': {b.code[:3]: b for b in Branch.objects.all()}, 'services': []}
    own = Command._order(ctx, client, 'ревьюер', [_box('Посылка', '2.0')])
    Order.objects.filter(id=own.id).update(comment='Мой заказ')
    Command._advance(ctx, own, PAID_CHAIN[:3])
    PaymentService.register(actor=admin, order=own, amount=Decimal('100'), payment_method=PaymentMethod.CASH)
    Incident.objects.create(
        shipment=Shipment.objects.get(status=ShipmentStatus.IN_TRANSIT), type='delay', description='Пробка'
    )
    assert snapshot() != initial

    out = StringIO()
    call_command('seed_demo', '--reset-scenarios', stdout=out)

    assert snapshot() == initial
    assert 'reset: удалено заказов 9, рейсов 4' in out.getvalue()
    assert not Incident.all_objects.exists()
