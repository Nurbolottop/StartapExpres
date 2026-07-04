"""Селекторы warehouses: только чтение."""

from django.db.models import F, QuerySet

from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone


class WarehouseSelector:
    @staticmethod
    def list() -> QuerySet[Warehouse]:
        return Warehouse.objects.select_related('branch', 'manager')

    @staticmethod
    def zones() -> QuerySet[WarehouseZone]:
        return WarehouseZone.objects.select_related('warehouse')

    @staticmethod
    def cells() -> QuerySet[WarehouseCell]:
        return WarehouseCell.objects.select_related('zone__warehouse')

    @staticmethod
    def available_cells() -> QuerySet[WarehouseCell]:
        """Ячейки со свободной вместимостью (ТЗ, раздел 08)."""
        return WarehouseSelector.cells().filter(
            is_active=True,
            occupied_weight__lt=F('capacity_weight'),
            occupied_volume__lt=F('capacity_volume'),
        )
