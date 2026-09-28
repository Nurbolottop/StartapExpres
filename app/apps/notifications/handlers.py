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

# Водитель отметил точку маршрута: уведомляем клиентов всех заказов рейса
CHECKPOINT_EVENT = 'shipment.checkpoint_reached'


def handle_event(event: events.Event) -> None:
    if event.type == CHECKPOINT_EVENT:
        _handle_checkpoint(event)
        return
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


def _handle_checkpoint(event: events.Event) -> None:
    from apps.notifications.choices import NotificationType
    from apps.notifications.services import NotificationService
    from apps.orders.models import Order

    city = event.payload.get('city_name', '')
    orders = Order.objects.select_related('client').filter(id__in=event.payload.get('order_ids', []))
    for order in orders:
        NotificationService.create(
            user=order.client,
            event_type=event.type,
            context={
                'client': order.client.full_name or order.client.phone,
                'order': order.order_number,
                'city': city,
            },
            channels=(NotificationType.IN_APP, NotificationType.PUSH),
        )


def register() -> None:
    events.dispatcher.subscribe(events.WILDCARD, handle_event)
