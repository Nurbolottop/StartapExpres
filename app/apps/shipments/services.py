"""Сервисный слой shipments (ТЗ, раздел 09).

Создание рейса, назначения, состав, погрузка сканами, жизненный цикл,
инциденты. Инварианты раздела 22: одна машина/водитель/заказ — один
активный рейс; состав заморожен после старта.
"""

from django.db import transaction
from django.utils import timezone

from apps.common import events
from apps.common.services import generate_number
from apps.orders.choices import OrderStatus
from apps.orders.models import Order
from apps.orders.transitions import OrderTransitionService
from apps.packages.choices import PackageStatus
from apps.packages.models import Package
from apps.packages.transitions import PackageTransitionService
from apps.shipments import exceptions
from apps.shipments.choices import (
    ACTIVE_STATUSES,
    OPEN_STATUSES,
    SHIPMENT_TRANSITION_ROLES,
    SHIPMENT_TRANSITIONS,
    STARTED_STATUSES,
    ShipmentStatus,
)
from apps.shipments.models import Incident, Shipment, ShipmentItem, ShipmentStatusHistory
from apps.tracking.services import TrackingService
from apps.users.choices import DriverStatus, Roles
from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle
from apps.warehouses.operations import WarehouseOperationsService


class ShipmentTransitionService:
    @staticmethod
    def can_change(shipment: Shipment, to_status: str) -> bool:
        return to_status in SHIPMENT_TRANSITIONS.get(shipment.status, frozenset())

    @classmethod
    def validate(cls, shipment: Shipment, to_status: str, actor) -> None:
        if not cls.can_change(shipment, to_status):
            raise exceptions.InvalidShipmentTransitionException(
                f'Переход {shipment.status} → {to_status} запрещён.',
                details={'from': shipment.status, 'to': to_status},
            )
        allowed = SHIPMENT_TRANSITION_ROLES.get(to_status, frozenset())
        if actor.role not in allowed and not actor.is_superuser:
            raise exceptions.ShipmentTransitionRoleException()
        if actor.role == Roles.DRIVER and shipment.driver_id != actor.id:
            raise exceptions.ShipmentTransitionRoleException('Водитель может управлять только своим рейсом.')

    @classmethod
    @transaction.atomic
    def change(cls, *, shipment: Shipment, to_status: str, actor, comment: str = '') -> Shipment:
        locked = Shipment.objects.select_for_update().get(id=shipment.id)
        cls.validate(locked, to_status, actor)

        from_status = locked.status
        locked.status = to_status
        locked.version += 1
        locked.updated_by = actor
        locked.save(update_fields=['status', 'version', 'updated_by', 'updated_at'])
        ShipmentStatusHistory.objects.create(
            shipment=locked,
            from_status=from_status,
            to_status=to_status,
            changed_by=actor,
            comment=comment,
        )
        events.publish(
            f'shipment.{to_status}',
            {
                'actor_id': str(actor.id),
                'model': 'Shipment',
                'object_id': str(locked.id),
                'action': f'status_{to_status}',
                'old': {'status': from_status},
                'new': {'status': to_status},
            },
            source='shipments',
        )
        shipment.status = locked.status
        shipment.version = locked.version
        return locked


class ShipmentService:
    @staticmethod
    def _check_vehicle_free(vehicle: Vehicle, exclude_shipment=None) -> None:
        busy = Shipment.objects.filter(vehicle=vehicle, status__in=ACTIVE_STATUSES)
        if exclude_shipment:
            busy = busy.exclude(id=exclude_shipment.id)
        if busy.exists():
            raise exceptions.VehicleBusyException()
        if not vehicle.is_active or vehicle.status in (VehicleStatus.MAINTENANCE, VehicleStatus.INACTIVE):
            raise exceptions.VehicleBusyException('Автомобиль неактивен или на обслуживании.')

    @staticmethod
    def _check_driver_free(driver, exclude_shipment=None) -> None:
        if driver.role != Roles.DRIVER or not driver.is_active:
            raise exceptions.DriverBusyException('Пользователь не является активным водителем.')
        busy = Shipment.objects.filter(driver=driver, status__in=ACTIVE_STATUSES)
        if exclude_shipment:
            busy = busy.exclude(id=exclude_shipment.id)
        if busy.exists():
            raise exceptions.DriverBusyException()

    @classmethod
    @transaction.atomic
    def create(
        cls,
        *,
        actor,
        departure_branch,
        arrival_branch,
        route=None,
        vehicle=None,
        driver=None,
        planned_departure=None,
    ) -> Shipment:
        if vehicle:
            cls._check_vehicle_free(vehicle)
        if driver:
            cls._check_driver_free(driver)
        shipment = Shipment(
            shipment_number=generate_number('SHP'),
            departure_branch=departure_branch,
            arrival_branch=arrival_branch,
            route=route,
            vehicle=vehicle,
            driver=driver,
            planned_departure=planned_departure,
            created_by=actor,
        )
        shipment.full_clean()
        shipment.save()
        events.publish(
            'shipment.created',
            {
                'actor_id': str(actor.id),
                'model': 'Shipment',
                'object_id': str(shipment.id),
                'action': 'create',
                'new': {'shipment_number': shipment.shipment_number},
            },
            source='shipments',
        )
        return shipment

    @classmethod
    @transaction.atomic
    def assign_vehicle(cls, *, actor, shipment: Shipment, vehicle: Vehicle) -> Shipment:
        cls._ensure_editable(shipment)
        cls._check_vehicle_free(vehicle, exclude_shipment=shipment)
        shipment.vehicle = vehicle
        shipment.updated_by = actor
        shipment.save(update_fields=['vehicle', 'updated_by', 'updated_at'])
        return shipment

    @classmethod
    @transaction.atomic
    def assign_driver(cls, *, actor, shipment: Shipment, driver) -> Shipment:
        cls._ensure_editable(shipment)
        cls._check_driver_free(driver, exclude_shipment=shipment)
        shipment.driver = driver
        shipment.updated_by = actor
        shipment.save(update_fields=['driver', 'updated_by', 'updated_at'])
        return shipment

    @staticmethod
    def _ensure_editable(shipment: Shipment) -> None:
        if shipment.status in STARTED_STATUSES or shipment.status in (
            ShipmentStatus.COMPLETED,
            ShipmentStatus.CANCELLED,
            ShipmentStatus.FAILED,
        ):
            raise exceptions.ShipmentLockedException()

    @classmethod
    def _capacity_check(cls, shipment: Shipment, extra_orders: list[Order]) -> None:
        if shipment.vehicle is None:
            return
        packages = Package.objects.filter(shipment_items__shipment=shipment)
        weight = sum((p.weight for p in packages), start=0)
        volume = sum((p.volume for p in packages), start=0)
        for order in extra_orders:
            for package in order.packages.all():
                weight += package.weight
                volume += package.volume
        if weight > shipment.vehicle.max_weight:
            raise exceptions.WeightLimitException(
                details={'total_weight': str(weight), 'max_weight': str(shipment.vehicle.max_weight)}
            )
        if volume > shipment.vehicle.max_volume:
            raise exceptions.VolumeLimitException(
                details={'total_volume': str(volume), 'max_volume': str(shipment.vehicle.max_volume)}
            )

    @classmethod
    @transaction.atomic
    def add_order(cls, *, actor, shipment: Shipment, order: Order) -> Shipment:
        """Только оплаченные заказы, готовые к отправке; заказ — в одном
        активном рейсе (ТЗ, разделы 09, 22)."""
        cls._ensure_editable(shipment)
        if order.status != OrderStatus.WAITING_SHIPMENT:
            raise exceptions.OrderNotReadyException(details={'status': order.status})
        in_active = (
            ShipmentItem.objects.filter(order=order, shipment__status__in=OPEN_STATUSES)
            .exclude(shipment=shipment)
            .exists()
        )
        if in_active or ShipmentItem.objects.filter(order=order, shipment=shipment).exists():
            raise exceptions.OrderAlreadyInShipmentException()
        cls._capacity_check(shipment, [order])

        for package in order.packages.all():
            ShipmentItem.objects.create(shipment=shipment, order=order, package=package, created_by=actor)
            PackageTransitionService.change(
                package=package, to_status=PackageStatus.WAITING_LOADING, actor=actor
            )
        events.publish(
            'shipment.order_added',
            {
                'actor_id': str(actor.id),
                'model': 'Shipment',
                'object_id': str(shipment.id),
                'action': 'add_order',
                'new': {'order': order.order_number},
            },
            source='shipments',
        )
        return shipment

    @classmethod
    @transaction.atomic
    def remove_order(cls, *, actor, shipment: Shipment, order: Order) -> Shipment:
        cls._ensure_editable(shipment)
        items = ShipmentItem.objects.filter(shipment=shipment, order=order)
        for item in items:
            if item.package.status == PackageStatus.WAITING_LOADING:
                item.package.status = PackageStatus.STORED
                item.package.updated_by = actor
                item.package.save(update_fields=['status', 'updated_by', 'updated_at'])
        items.delete()
        return shipment

    @staticmethod
    @transaction.atomic
    def load_package(*, actor, shipment: Shipment, qr_code: str) -> ShipmentItem:
        """Погрузка только по скану QR (ТЗ, разделы 04, 08, 09)."""
        item = (
            ShipmentItem.objects.select_related('package', 'order')
            .filter(shipment=shipment, package__qr_code=qr_code)
            .first()
        )
        if item is None:
            raise exceptions.MissingPackageException('Груз с таким QR не входит в рейс.')
        if item.loaded_at is None:
            package = item.package
            if package.current_cell:
                WarehouseOperationsService._release_cell(package.current_cell, package)
                package.current_cell = None
                package.save(update_fields=['current_cell', 'updated_at'])
            PackageTransitionService.change(package=package, to_status=PackageStatus.LOADED, actor=actor)
            item.loaded_at = timezone.now()
            item.updated_by = actor
            item.save(update_fields=['loaded_at', 'updated_by', 'updated_at'])
            TrackingService.record(
                order=item.order, package=package, status=PackageStatus.LOADED, employee=actor
            )
        return item

    @classmethod
    @transaction.atomic
    def finish_loading(cls, *, actor, shipment: Shipment) -> Shipment:
        """Завершение погрузки: без единого непросканированного груза (ТЗ, раздел 09)."""
        if shipment.items.filter(loaded_at__isnull=True).exists():
            raise exceptions.MissingPackageException()
        if not shipment.items.exists():
            raise exceptions.MissingPackageException('В рейсе нет грузов.')
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.LOADED, actor=actor
        )
        order_ids = shipment.items.values_list('order_id', flat=True).distinct()
        for order in Order.objects.filter(id__in=order_ids):
            if OrderTransitionService.can_change(order, OrderStatus.LOADED):
                OrderTransitionService.change(order=order, to_status=OrderStatus.LOADED, actor=actor)
        return shipment

    @classmethod
    @transaction.atomic
    def start(cls, *, actor, shipment: Shipment) -> Shipment:
        """Старт рейса: чек-лист раздела 09, затем STARTED → IN_TRANSIT."""
        problems = []
        if shipment.driver is None:
            problems.append('не назначен водитель')
        if shipment.vehicle is None:
            problems.append('не назначен автомобиль')
        if shipment.route is None:
            problems.append('не выбран маршрут')
        if not shipment.items.exists():
            problems.append('нет грузов')
        if shipment.items.filter(loaded_at__isnull=True).exists():
            problems.append('не все QR отсканированы')
        if problems:
            raise exceptions.ShipmentChecklistException(details={'problems': problems})

        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.STARTED, actor=actor
        )
        shipment.departure_time = timezone.now()
        shipment.save(update_fields=['departure_time', 'updated_at'])
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.IN_TRANSIT, actor=actor
        )

        Vehicle.objects.filter(id=shipment.vehicle_id).update(status=VehicleStatus.BUSY)
        profile = getattr(shipment.driver, 'driver_profile', None)
        if profile:
            profile.status = DriverStatus.ON_TRIP
            profile.save(update_fields=['status', 'updated_at'])

        order_ids = shipment.items.values_list('order_id', flat=True).distinct()
        for order in Order.objects.filter(id__in=order_ids):
            if OrderTransitionService.can_change(order, OrderStatus.IN_TRANSIT):
                OrderTransitionService.change(order=order, to_status=OrderStatus.IN_TRANSIT, actor=actor)
        for item in shipment.items.select_related('package'):
            if PackageTransitionService.can_change(item.package, PackageStatus.IN_TRANSIT):
                PackageTransitionService.change(
                    package=item.package, to_status=PackageStatus.IN_TRANSIT, actor=actor
                )
        return shipment

    @classmethod
    @transaction.atomic
    def arrive(cls, *, actor, shipment: Shipment) -> Shipment:
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.ARRIVED, actor=actor
        )
        shipment.arrival_time = timezone.now()
        shipment.save(update_fields=['arrival_time', 'updated_at'])
        order_ids = shipment.items.values_list('order_id', flat=True).distinct()
        for order in Order.objects.filter(id__in=order_ids):
            if OrderTransitionService.can_change(order, OrderStatus.ARRIVED):
                OrderTransitionService.change(order=order, to_status=OrderStatus.ARRIVED, actor=actor)
        return shipment

    @staticmethod
    @transaction.atomic
    def unload_package(*, actor, shipment: Shipment, qr_code: str) -> ShipmentItem:
        """Разгрузка только по повторному скану (ТЗ, разделы 08, 09)."""
        if shipment.status != ShipmentStatus.UNLOADING:
            raise exceptions.InvalidShipmentTransitionException('Рейс не в статусе разгрузки.')
        item = (
            ShipmentItem.objects.select_related('package', 'order')
            .filter(shipment=shipment, package__qr_code=qr_code)
            .first()
        )
        if item is None:
            raise exceptions.MissingPackageException('Груз с таким QR не входит в рейс.')
        if item.unloaded_at is None:
            PackageTransitionService.change(
                package=item.package, to_status=PackageStatus.UNLOADED, actor=actor
            )
            item.unloaded_at = timezone.now()
            item.updated_by = actor
            item.save(update_fields=['unloaded_at', 'updated_by', 'updated_at'])
            TrackingService.record(
                order=item.order, package=item.package, status=PackageStatus.UNLOADED, employee=actor
            )
        return item

    @classmethod
    @transaction.atomic
    def finish(cls, *, actor, shipment: Shipment) -> Shipment:
        """Завершение: все грузы разгружены (ТЗ, раздел 22); заказы готовы к выдаче."""
        if shipment.items.filter(unloaded_at__isnull=True).exists():
            raise exceptions.MissingPackageException('Не все грузы разгружены.')
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.COMPLETED, actor=actor
        )
        Vehicle.objects.filter(id=shipment.vehicle_id).update(status=VehicleStatus.AVAILABLE)
        profile = getattr(shipment.driver, 'driver_profile', None)
        if profile:
            profile.status = DriverStatus.AVAILABLE
            profile.save(update_fields=['status', 'updated_at'])

        for item in shipment.items.select_related('package'):
            if PackageTransitionService.can_change(item.package, PackageStatus.READY_FOR_PICKUP):
                PackageTransitionService.change(
                    package=item.package, to_status=PackageStatus.READY_FOR_PICKUP, actor=actor
                )
        order_ids = shipment.items.values_list('order_id', flat=True).distinct()
        for order in Order.objects.filter(id__in=order_ids):
            if OrderTransitionService.can_change(order, OrderStatus.READY_FOR_PICKUP):
                OrderTransitionService.change(
                    order=order, to_status=OrderStatus.READY_FOR_PICKUP, actor=actor
                )
        return shipment

    @classmethod
    @transaction.atomic
    def cancel(cls, *, actor, shipment: Shipment, comment: str = '') -> Shipment:
        """Отмена возможна только до старта (ТЗ, раздел 09)."""
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.CANCELLED, actor=actor, comment=comment
        )
        for item in shipment.items.select_related('package'):
            package = item.package
            if package.status in (PackageStatus.WAITING_LOADING, PackageStatus.LOADED):
                package.status = PackageStatus.STORED
                package.updated_by = actor
                package.save(update_fields=['status', 'updated_by', 'updated_at'])
        return shipment

    @staticmethod
    @transaction.atomic
    def report_incident(
        *,
        actor,
        shipment: Shipment,
        incident_type: str,
        description: str,
        photo=None,
        latitude=None,
        longitude=None,
    ) -> Incident:
        incident = Incident.objects.create(
            shipment=shipment,
            type=incident_type,
            description=description,
            photo=photo,
            latitude=latitude,
            longitude=longitude,
            created_by=actor,
        )
        events.publish(
            'shipment.incident',
            {
                'actor_id': str(actor.id),
                'model': 'Incident',
                'object_id': str(incident.id),
                'action': 'report_incident',
                'new': {'type': incident_type, 'shipment': shipment.shipment_number},
            },
            source='shipments',
        )
        return incident
