"""Сервисный слой branches: запись справочников городов и филиалов."""

from django.db import transaction

from apps.branches.models import Branch, City
from apps.common import events


class _ReferenceService:
    """Общая логика справочников: создание/изменение/soft delete + события."""

    model: type
    event_prefix: str

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
                'new': {'name': instance.name, 'code': instance.code},
            },
            source='branches',
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
            source='branches',
        )
        return instance

    @classmethod
    @transaction.atomic
    def soft_delete(cls, *, actor, instance) -> None:
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
            source='branches',
        )


class CityService(_ReferenceService):
    model = City
    event_prefix = 'city'


class BranchService(_ReferenceService):
    model = Branch
    event_prefix = 'branch'
