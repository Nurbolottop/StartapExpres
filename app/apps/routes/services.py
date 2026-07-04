"""Сервисный слой routes."""

from django.db import transaction

from apps.common import events
from apps.routes.models import Route, RoutePoint


class _CrudService:
    model: type
    event_prefix: str
    source = 'routes'

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


class RouteService(_CrudService):
    model = Route
    event_prefix = 'route'


class RoutePointService(_CrudService):
    model = RoutePoint
    event_prefix = 'route_point'
