"""Сервисный слой warehouses: справочная структура склада.

Складские процессы (приём, размещение, погрузка) — Этап 3 по Roadmap.
Бизнес-ограничения удаления — ТЗ, раздел 22.
"""

from django.db import transaction

from apps.common import events
from apps.warehouses import exceptions
from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone


class _CrudService:
    model: type
    event_prefix: str
    source = 'warehouses'

    @classmethod
    def _check_delete(cls, instance) -> None:
        """Переопределяется наследниками для бизнес-ограничений удаления."""

    @classmethod
    @transaction.atomic
    def create(cls, *, actor, data: dict):
        instance = cls.model(created_by=actor, **data)
        instance.full_clean()
        instance.save()
        events.publish(
            f'{cls.event_prefix}.created',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'create',
                'new': {'repr': str(instance)},
            },
            source=cls.source,
        )
        return instance

    @classmethod
    @transaction.atomic
    def update(cls, *, actor, instance, data: dict):
        old = {field: str(getattr(instance, field)) for field in data}
        for field, value in data.items():
            setattr(instance, field, value)
        instance.updated_by = actor
        instance.full_clean()
        instance.save()
        events.publish(
            f'{cls.event_prefix}.updated',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'update',
                'old': old,
                'new': {field: str(getattr(instance, field)) for field in old},
            },
            source=cls.source,
        )
        return instance

    @classmethod
    @transaction.atomic
    def soft_delete(cls, *, actor, instance) -> None:
        cls._check_delete(instance)
        instance.updated_by = actor
        instance.is_active = False
        instance.save(update_fields=['updated_by', 'is_active', 'updated_at'])
        instance.delete()
        events.publish(
            f'{cls.event_prefix}.deleted',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'soft_delete',
            },
            source=cls.source,
        )


class WarehouseService(_CrudService):
    model = Warehouse
    event_prefix = 'warehouse'

    @classmethod
    def _check_delete(cls, instance) -> None:
        if instance.zones.exists():
            raise exceptions.WarehouseNotEmptyException()


class ZoneService(_CrudService):
    model = WarehouseZone
    event_prefix = 'warehouse_zone'

    @classmethod
    def _check_delete(cls, instance) -> None:
        if instance.cells.exists():
            raise exceptions.ZoneNotEmptyException()


class CellService(_CrudService):
    model = WarehouseCell
    event_prefix = 'warehouse_cell'

    @classmethod
    def _check_delete(cls, instance) -> None:
        if instance.occupied_weight > 0 or instance.occupied_volume > 0:
            raise exceptions.CellNotEmptyException()
