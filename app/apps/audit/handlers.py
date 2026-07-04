"""Подписчик Event Bus: каждое доменное событие фиксируется в аудите
(ТЗ, раздел 17: OrderPaid → ... → AuditService)."""

import logging

from apps.common import events
from apps.common.logging import request_context

logger = logging.getLogger(__name__)


def handle_event(event: events.Event) -> None:
    from apps.audit.models import AuditLog
    from apps.users.models import User

    payload = event.payload
    context = request_context.get()

    actor = None
    actor_id = payload.get('actor_id')
    if actor_id:
        actor = User.objects.filter(id=actor_id).first()

    AuditLog.objects.create(
        user=actor,
        role=actor.role if actor else '',
        model=payload.get('model', ''),
        object_uuid=str(payload.get('object_id', '')),
        action=payload.get('action', event.type),
        event_type=event.type,
        old_data=payload.get('old', {}),
        new_data=payload.get('new', {}),
        ip=context.get('ip') or None,
        user_agent=context.get('user_agent', ''),
        request_id=context.get('request_id', ''),
    )


def register() -> None:
    events.dispatcher.subscribe(events.WILDCARD, handle_event)
