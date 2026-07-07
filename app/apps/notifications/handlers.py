"""Подписчик Event Bus: события жизненного цикла заказа → уведомления клиенту
(ТЗ, разделы 04, 12)."""

import logging

from apps.common import events

logger = logging.getLogger('notifications')

# 10 событий цепочки уведомлений (ТЗ, раздел 04)
CLIENT_ORDER_EVENTS = frozenset(
    {
        'order.created',
        'order.confirmed',
        'order.paid',
        'order.received',
        'order.loaded',
        'order.in_transit',
        'order.arrived',
        'order.ready_for_pickup',
        'order.delivered',
        'order.completed',
    }
)


def handle_event(event: events.Event) -> None:
    if event.type not in CLIENT_ORDER_EVENTS:
        return
    from apps.notifications.choices import NotificationType
    from apps.notifications.services import NotificationService
    from apps.orders.models import Order

    order = Order.objects.select_related('client').filter(id=event.payload.get('object_id')).first()
    if order is None:
        return
    NotificationService.create(
        user=order.client,
        event_type=event.type,
        context={
            'client': order.client.full_name or order.client.phone,
            'order': order.order_number,
            'price': order.total_price,
        },
        channels=(NotificationType.IN_APP, NotificationType.PUSH),
    )


def register() -> None:
    events.dispatcher.subscribe(events.WILDCARD, handle_event)
