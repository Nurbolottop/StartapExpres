"""Сервисный слой orders (ТЗ, раздел 07).

Создание, редактирование (с заморозкой полей), подтверждение, отмена, оплата.
Полноценный финансовый контур (Payment/Invoice/Transaction) — Этап 6;
здесь фиксируются статусы оплаты и paid_amount.
"""

from decimal import Decimal

from django.db import transaction

from apps.common import events
from apps.common.services import generate_number
from apps.orders import exceptions
from apps.orders.choices import (
    EDITABLE_STATUSES,
    FROZEN_AFTER_CONFIRM,
    SHIPPED_STATUSES,
    OrderStatus,
)
from apps.orders.models import Order, OrderServiceItem
from apps.orders.transitions import OrderTransitionService
from apps.packages.models import Package
from apps.tariffs.services import TariffService
from apps.tracking.services import TrackingService
from apps.users.choices import Roles

ORDER_FIELDS = frozenset(
    {
        'sender_name',
        'sender_phone',
        'sender_address',
        'receiver_name',
        'receiver_phone',
        'receiver_address',
        'from_branch',
        'to_branch',
        'payment_type',
        'delivery_type',
        'comment',
    }
)


class OrderService:
    @staticmethod
    def _calculate_price(order_data: dict, packages_data: list[dict], services) -> dict:
        from_city = order_data['from_branch'].city
        to_city = order_data['to_branch'].city
        total_weight = sum((item['weight'] for item in packages_data), Decimal('0'))
        total_volume = Decimal('0')
        declared = Decimal('0')
        for item in packages_data:
            volume = item.get('volume') or Decimal('0')
            if not volume and item.get('length') and item.get('width') and item.get('height'):
                volume = Decimal(item['length'] * item['width'] * item['height']) / Decimal('1000000')
            total_volume += volume
            declared += item.get('declared_price') or Decimal('0')
        return TariffService.calculate(
            from_city=from_city,
            to_city=to_city,
            weight=total_weight,
            volume=total_volume,
            declared_value=declared,
            services=list(services),
        )

    @classmethod
    @transaction.atomic
    def create(cls, *, actor, client, packages: list[dict], services=(), **order_data) -> Order:
        """Создание заказа клиентом или оператором (ТЗ, раздел 07)."""
        if not packages:
            raise exceptions.PackagesRequiredException()

        price = cls._calculate_price(order_data, packages, services)
        order = Order(
            order_number=generate_number('ORD'),
            client=client,
            tariff=price['tariff'],
            total_price=price['total_price'],
            insurance_price=price['insurance_price'],
            price_details={key: str(value) for key, value in price.items() if key != 'tariff'},
            created_by=actor,
            **order_data,
        )
        order.full_clean()
        order.save()

        for item in packages:
            package = Package(order=order, created_by=actor, **item)
            package.full_clean()
            package.save()
        for service in services:
            OrderServiceItem.objects.create(
                order=order, service=service, price=service.price, created_by=actor
            )

        TrackingService.record(order=order, status=OrderStatus.DRAFT, employee=actor)
        events.publish(
            'order.created',
            {
                'actor_id': str(actor.id),
                'model': 'Order',
                'object_id': str(order.id),
                'action': 'create',
                'new': {'order_number': order.order_number, 'total_price': str(order.total_price)},
            },
            source='orders',
        )
        return order

    @classmethod
    @transaction.atomic
    def update(cls, *, actor, order: Order, data: dict) -> Order:
        """Редактирование: свободно до подтверждения; после — только
        незамороженные поля; после отправки — запрещено (ТЗ, разделы 07, 22)."""
        if order.status in SHIPPED_STATUSES:
            raise exceptions.OrderLockedException()

        unknown = set(data) - ORDER_FIELDS
        if unknown:
            raise exceptions.FrozenFieldsException(
                f'Поля недоступны для изменения: {", ".join(sorted(unknown))}.'
            )
        if order.status not in EDITABLE_STATUSES:
            frozen = set(data) & FROZEN_AFTER_CONFIRM
            if frozen:
                raise exceptions.FrozenFieldsException(details={'frozen_fields': sorted(frozen)})

        old = {field: str(getattr(order, field)) for field in data}
        for field, value in data.items():
            setattr(order, field, value)
        order.updated_by = actor
        order.full_clean()
        order.save()
        events.publish(
            'order.updated',
            {
                'actor_id': str(actor.id),
                'model': 'Order',
                'object_id': str(order.id),
                'action': 'update',
                'old': old,
                'new': {field: str(getattr(order, field)) for field in old},
            },
            source='orders',
        )
        return order

    @staticmethod
    def submit(*, actor, order: Order) -> Order:
        """Черновик → на проверку оператору."""
        return OrderTransitionService.change(
            order=order, to_status=OrderStatus.WAITING_CONFIRMATION, actor=actor
        )

    @staticmethod
    def confirm(*, actor, order: Order) -> Order:
        """Подтверждение оператором; заказ сразу ожидает оплату (ТЗ, раздел 07)."""
        order = OrderTransitionService.change(order=order, to_status=OrderStatus.CONFIRMED, actor=actor)
        return OrderTransitionService.change(order=order, to_status=OrderStatus.WAITING_PAYMENT, actor=actor)

    @staticmethod
    def need_correction(*, actor, order: Order, comment: str) -> Order:
        return OrderTransitionService.change(
            order=order, to_status=OrderStatus.NEED_CORRECTION, actor=actor, comment=comment
        )

    @staticmethod
    def cancel(*, actor, order: Order, comment: str = '') -> Order:
        return OrderTransitionService.change(
            order=order, to_status=OrderStatus.CANCELLED, actor=actor, comment=comment
        )

    @classmethod
    @transaction.atomic
    def pay(cls, *, actor, order: Order, amount: Decimal) -> Order:
        """Фиксация оплаты (ТЗ, разделы 07, 11): полная или частичная.

        Полноценные Payment/Invoice/Transaction создаются модулем finance (Этап 6).
        """
        locked = Order.objects.select_for_update().get(id=order.id)
        if locked.status == OrderStatus.PAID or locked.paid_amount >= locked.total_price:
            raise exceptions.OrderAlreadyPaidException()

        locked.paid_amount = locked.paid_amount + amount
        locked.updated_by = actor
        locked.save(update_fields=['paid_amount', 'updated_by', 'updated_at'])

        if locked.paid_amount >= locked.total_price:
            locked = OrderTransitionService.change(
                order=locked,
                to_status=OrderStatus.PAID,
                actor=actor,
                comment=f'Оплата {amount}',
            )
            locked = OrderTransitionService.change(
                order=locked, to_status=OrderStatus.WAITING_RECEIVE, actor=actor
            )
        elif locked.status != OrderStatus.PARTIALLY_PAID:
            locked = OrderTransitionService.change(
                order=locked,
                to_status=OrderStatus.PARTIALLY_PAID,
                actor=actor,
                comment=f'Частичная оплата {amount}',
            )
        events.publish(
            'order.payment_registered',
            {
                'actor_id': str(actor.id),
                'model': 'Order',
                'object_id': str(locked.id),
                'action': 'pay',
                'new': {'amount': str(amount), 'paid_amount': str(locked.paid_amount)},
            },
            source='orders',
        )
        return locked

    @staticmethod
    def check_owner(order: Order, user) -> bool:
        return order.client_id == user.id or user.role != Roles.CLIENT
