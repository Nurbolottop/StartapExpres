"""Событийная шина (ТЗ, раздел 17).

Сервисы публикуют доменные события через dispatcher; подписчики (audit,
notifications, analytics) реагируют независимо. В v1 доставка синхронная
внутри процесса; транспорт можно заменить на Celery/Kafka без изменения
кода публикации.
"""

import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from django.utils import timezone

logger = logging.getLogger(__name__)

WILDCARD = '*'


@dataclass(frozen=True)
class Event:
    type: str
    payload: dict[str, Any]
    source: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    version: int = 1
    occurred_at: str = field(default_factory=lambda: timezone.now().isoformat())


class EventDispatcher:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Подписка на тип события; WILDCARD — на все события."""
        self._handlers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        """Ошибка одного подписчика не должна ронять операцию и других подписчиков."""
        handlers = self._handlers.get(event.type, []) + self._handlers.get(WILDCARD, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception('Ошибка обработчика %s для события %s', handler, event.type)


dispatcher = EventDispatcher()


def publish(event_type: str, payload: dict[str, Any], *, source: str) -> Event:
    event = Event(type=event_type, payload=payload, source=source)
    dispatcher.publish(event)
    return event
