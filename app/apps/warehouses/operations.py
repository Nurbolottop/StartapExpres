"""Складские процессы (ТЗ, раздел 08): приём → проверка → размещение →
перемещение → инвентаризация → выдача. Повреждения и утери.

Погрузка/разгрузка выполняются модулем shipments (Этап 4) через эти же
package-переходы.
"""

from django.db import transaction
from django.utils import timezone

from apps.common import events
from apps.orders.choices import OrderStatus
from apps.orders.models import Order
from apps.orders.transitions import OrderTransitionService
from apps.packages.choices import PackageStatus, PhotoType
from apps.packages.models import Package
from apps.packages.transitions import PackageTransitionService
from apps.tracking.services import TrackingService
from apps.warehouses import exceptions
from apps.warehouses.models import (
    DamageReport,
    DeliveryConfirmation,
    InventoryScan,
    InventorySession,
    LostReport,
    WarehouseCell,
    WarehouseMovement,
)


class PhotoRequiredException(exceptions.CellFullException):
    default_code = 'WAREHOUSE_004'
    default_message = 'Операция требует фотофиксации (ТЗ, раздел 08).'


def _require_photo(package: Package, photo_type: str) -> None:
    if not package.photos.filter(type=photo_type).exists():
        raise PhotoRequiredException(f'Нет фото этапа «{photo_type}» — операция не может быть завершена.')


def _sync_order_status(order: Order, actor, all_packages_status: str, order_target: str) -> None:
    """Если все грузы заказа достигли статуса — заказ переводится следом."""
    if OrderTransitionService.can_change(order, order_target) and not (
        order.packages.exclude(status=all_packages_status).exists()
    ):
        OrderTransitionService.change(order=order, to_status=order_target, actor=actor)


class WarehouseOperationsService:
    @staticmethod
    @transaction.atomic
    def receive(*, actor, package: Package) -> Package:
        """Приём груза: обязательна фотофиксация (ТЗ, раздел 08)."""
        _require_photo(package, PhotoType.RECEIVING)
        PackageTransitionService.change(package=package, to_status=PackageStatus.RECEIVED, actor=actor)
        TrackingService.record(
            order=package.order, package=package, status=PackageStatus.RECEIVED, employee=actor
        )
        _sync_order_status(package.order, actor, PackageStatus.RECEIVED, OrderStatus.RECEIVED)
        events.publish(
            'package.received',
            {
                'actor_id': str(actor.id),
                'model': 'Package',
                'object_id': str(package.id),
                'action': 'receive',
            },
            source='warehouses',
        )
        return package

    @staticmethod
    @transaction.atomic
    def check(*, actor, package: Package, weight=None, length=None, width=None, height=None) -> Package:
        """Проверка, взвешивание и обмер. После фиксации вес/габариты заморожены
        (ТЗ, раздел 08): менять их дальше может только Director/SuperAdmin."""
        updates = []
        if weight is not None:
            package.weight = weight
            updates.append('weight')
        for field, value in (('length', length), ('width', width), ('height', height)):
            if value is not None:
                setattr(package, field, value)
                updates.append(field)
        if {'length', 'width', 'height'} & set(updates):
            package.volume = 0  # пересчитается в save()
            updates.append('volume')
        PackageTransitionService.change(package=package, to_status=PackageStatus.CHECKED, actor=actor)
        if updates:
            package.save(update_fields=[*updates, 'updated_at'])
        TrackingService.record(
            order=package.order, package=package, status=PackageStatus.CHECKED, employee=actor
        )
        return package

    @staticmethod
    @transaction.atomic
    def store(*, actor, package: Package, cell: WarehouseCell, reason: str = '') -> Package:
        """Размещение в ячейку с контролем вместимости (ТЗ, разделы 08, 22)."""
        if not package.qr_code:
            raise exceptions.CellFullException('Груз без QR не может быть размещён.', code='WAREHOUSE_003')
        cell = WarehouseCell.objects.select_for_update().get(id=cell.id)
        if not cell.fits(package.weight, package.volume):
            raise exceptions.CellFullException()

        from_cell = package.current_cell
        if from_cell:
            WarehouseOperationsService._release_cell(from_cell, package)

        cell.occupied_weight += package.weight
        cell.occupied_volume += package.volume
        cell.save(update_fields=['occupied_weight', 'occupied_volume', 'updated_at'])
        package.current_cell = cell
        PackageTransitionService.change(package=package, to_status=PackageStatus.STORED, actor=actor)
        package.save(update_fields=['current_cell', 'updated_at'])

        WarehouseMovement.objects.create(
            package=package, from_cell=from_cell, to_cell=cell, reason=reason, created_by=actor
        )
        TrackingService.record(
            order=package.order,
            package=package,
            status=PackageStatus.STORED,
            employee=actor,
            comment=f'Ячейка {cell.code}',
        )
        _sync_order_status(package.order, actor, PackageStatus.STORED, OrderStatus.IN_WAREHOUSE)
        events.publish(
            'package.stored',
            {
                'actor_id': str(actor.id),
                'model': 'Package',
                'object_id': str(package.id),
                'action': 'store',
                'new': {'cell': cell.code},
            },
            source='warehouses',
        )
        return package

    @staticmethod
    def _release_cell(cell: WarehouseCell, package: Package) -> None:
        cell = WarehouseCell.objects.select_for_update().get(id=cell.id)
        cell.occupied_weight = max(cell.occupied_weight - package.weight, 0)
        cell.occupied_volume = max(cell.occupied_volume - package.volume, 0)
        cell.save(update_fields=['occupied_weight', 'occupied_volume', 'updated_at'])

    @classmethod
    @transaction.atomic
    def move(cls, *, actor, package: Package, to_cell: WarehouseCell, reason: str = '') -> Package:
        """Перемещение между ячейками с фиксацией истории (ТЗ, раздел 08)."""
        if package.current_cell_id is None:
            raise exceptions.CellFullException('Груз не размещён в ячейке.', code='WAREHOUSE_006')
        to_cell = WarehouseCell.objects.select_for_update().get(id=to_cell.id)
        if not to_cell.fits(package.weight, package.volume):
            raise exceptions.CellFullException()

        from_cell = package.current_cell
        cls._release_cell(from_cell, package)
        to_cell.occupied_weight += package.weight
        to_cell.occupied_volume += package.volume
        to_cell.save(update_fields=['occupied_weight', 'occupied_volume', 'updated_at'])
        package.current_cell = to_cell
        package.updated_by = actor
        package.save(update_fields=['current_cell', 'updated_by', 'updated_at'])

        WarehouseMovement.objects.create(
            package=package, from_cell=from_cell, to_cell=to_cell, reason=reason, created_by=actor
        )
        TrackingService.record(
            order=package.order,
            package=package,
            status='moved',
            employee=actor,
            comment=f'{from_cell.code} → {to_cell.code}',
        )
        return package

    @staticmethod
    @transaction.atomic
    def report_damage(*, actor, package: Package, description: str, reason: str = '') -> DamageReport:
        """Акт повреждения: фото обязательно (ТЗ, раздел 08)."""
        _require_photo(package, PhotoType.DAMAGE)
        report = DamageReport.objects.create(
            package=package, description=description, reason=reason, created_by=actor
        )
        PackageTransitionService.change(package=package, to_status=PackageStatus.DAMAGED, actor=actor)
        if package.current_cell:
            WarehouseOperationsService._release_cell(package.current_cell, package)
            package.current_cell = None
            package.save(update_fields=['current_cell', 'updated_at'])
        if OrderTransitionService.can_change(package.order, OrderStatus.DAMAGED):
            OrderTransitionService.change(
                order=package.order,
                to_status=OrderStatus.DAMAGED,
                actor=actor,
                comment=description,
            )
        events.publish(
            'package.damaged',
            {
                'actor_id': str(actor.id),
                'model': 'DamageReport',
                'object_id': str(report.id),
                'action': 'report_damage',
                'new': {'description': description},
            },
            source='warehouses',
        )
        return report

    @staticmethod
    @transaction.atomic
    def report_lost(*, actor, package: Package, description: str) -> LostReport:
        report = LostReport.objects.create(package=package, description=description, created_by=actor)
        PackageTransitionService.change(package=package, to_status=PackageStatus.LOST, actor=actor)
        if package.current_cell:
            WarehouseOperationsService._release_cell(package.current_cell, package)
            package.current_cell = None
            package.save(update_fields=['current_cell', 'updated_at'])
        if OrderTransitionService.can_change(package.order, OrderStatus.LOST):
            OrderTransitionService.change(
                order=package.order, to_status=OrderStatus.LOST, actor=actor, comment=description
            )
        events.publish(
            'package.lost',
            {
                'actor_id': str(actor.id),
                'model': 'LostReport',
                'object_id': str(report.id),
                'action': 'report_lost',
            },
            source='warehouses',
        )
        return report


class InventoryService:
    @staticmethod
    def open(*, actor, warehouse) -> InventorySession:
        session = InventorySession.objects.create(warehouse=warehouse, created_by=actor)
        events.publish(
            'inventory.opened',
            {
                'actor_id': str(actor.id),
                'model': 'InventorySession',
                'object_id': str(session.id),
                'action': 'open',
            },
            source='warehouses',
        )
        return session

    @staticmethod
    def scan(*, actor, session: InventorySession, qr_code: str) -> InventoryScan:
        from apps.packages.exceptions import PackageNotFoundByQRException

        if session.finished_at:
            raise exceptions.CellFullException('Инвентаризация завершена.', code='WAREHOUSE_005')
        package = Package.objects.filter(qr_code=qr_code).first()
        if package is None:
            raise PackageNotFoundByQRException()
        scan, _ = InventoryScan.objects.get_or_create(
            session=session, package=package, defaults={'created_by': actor}
        )
        return scan

    @staticmethod
    @transaction.atomic
    def close(*, actor, session: InventorySession) -> InventorySession:
        """Закрытие: расхождения (грузы склада без скана) — в отчёт (ТЗ, раздел 08)."""
        expected = Package.objects.filter(
            current_cell__zone__warehouse=session.warehouse,
            status=PackageStatus.STORED,
        )
        scanned_ids = set(session.scans.values_list('package_id', flat=True))
        missing = [str(package.id) for package in expected if package.id not in scanned_ids]

        session.finished_at = timezone.now()
        session.report = {
            'expected': expected.count(),
            'scanned': len(scanned_ids),
            'missing_packages': missing,
        }
        session.updated_by = actor
        session.save(update_fields=['finished_at', 'report', 'updated_by', 'updated_at'])
        events.publish(
            'inventory.closed',
            {
                'actor_id': str(actor.id),
                'model': 'InventorySession',
                'object_id': str(session.id),
                'action': 'close',
                'new': session.report,
            },
            source='warehouses',
        )
        return session


class DeliveryService:
    @staticmethod
    @transaction.atomic
    def issue(
        *,
        actor,
        order: Order,
        received_by_name: str,
        document_number: str,
        qr_codes: list[str],
        signature=None,
    ) -> DeliveryConfirmation:
        """Выдача заказа (ТЗ, разделы 04, 08): повторный скан каждого груза,
        документ получателя, подпись, фото выдачи."""
        packages = list(order.packages.all())
        scanned = set(qr_codes)
        for package in packages:
            if package.qr_code not in scanned:
                raise exceptions.CellFullException(
                    f'Груз {package.title} не отсканирован при выдаче.', code='WAREHOUSE_003'
                )
            _require_photo(package, PhotoType.DELIVERY)

        confirmation = DeliveryConfirmation.objects.create(
            order=order,
            received_by_name=received_by_name,
            document_number=document_number,
            signature=signature,
            created_by=actor,
        )
        for package in packages:
            PackageTransitionService.change(package=package, to_status=PackageStatus.DELIVERED, actor=actor)
            if package.current_cell:
                WarehouseOperationsService._release_cell(package.current_cell, package)
                package.current_cell = None
                package.save(update_fields=['current_cell', 'updated_at'])
        OrderTransitionService.change(
            order=order,
            to_status=OrderStatus.DELIVERED,
            actor=actor,
            comment=f'Выдан: {received_by_name}',
        )
        events.publish(
            'order.issued',
            {
                'actor_id': str(actor.id),
                'model': 'DeliveryConfirmation',
                'object_id': str(confirmation.id),
                'action': 'issue',
                'new': {'received_by': received_by_name},
            },
            source='warehouses',
        )
        return confirmation
