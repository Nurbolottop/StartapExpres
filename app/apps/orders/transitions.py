"""OrderTransitionService — единственная точка смены статуса заказа (ТЗ, раздел 23).

Пайплайн перехода: Validation → Permission → Business Rules → Transaction →
History → Tracking → Event (audit/notification — подписчики шины).
Optimistic locking: несовпадение version → 409.
"""

from django.db import transaction

from apps.common import events
from apps.orders import exceptions
from apps.orders.choices import STATUS_TRANSITIONS, TRANSITION_ALLOWED_ROLES, OrderStatus
from apps.orders.models import Order, OrderStatusHistory
from apps.tracking.services import TrackingService
from apps.users.choices import Roles


class OrderTransitionService:
    @staticmethod
    def can_change(order: Order, to_status: str) -> bool:
        return to_status in STATUS_TRANSITIONS.get(order.status, frozenset())

    @staticmethod
    def validate(order: Order, to_status: str, actor) -> None:
        if not OrderTransitionService.can_change(order, to_status):
            raise exceptions.InvalidStatusTransitionException(
                f'Переход {order.status} → {to_status} запрещён.',
                details={'from': order.status, 'to': to_status},
            )
        allowed_roles = TRANSITION_ALLOWED_ROLES.get(to_status, frozenset())
        if actor.role not in allowed_roles and not actor.is_superuser:
            raise exceptions.TransitionRoleException()
        if to_status == OrderStatus.COMPLETED:
            from apps.finance.exceptions import OrderFinanceIncompleteException
            from apps.finance.services import PaymentService

            if not PaymentService.is_order_settled(order):
                raise OrderFinanceIncompleteException()
        if to_status == OrderStatus.CANCELLED and actor.role == Roles.CLIENT:
            from apps.orders.choices import CLIENT_CANCELLABLE_STATUSES

            if order.status not in CLIENT_CANCELLABLE_STATUSES:
                raise exceptions.ClientCancelForbiddenException()

    @classmethod
    @transaction.atomic
    def change(
        cls,
        *,
        order: Order,
        to_status: str,
        actor,
        comment: str = '',
        expected_version: int | None = None,
    ) -> Order:
        locked = Order.objects.select_for_update().get(id=order.id)
        if expected_version is not None and locked.version != expected_version:
            raise exceptions.OrderVersionConflictException()

        cls.validate(locked, to_status, actor)

        from_status = locked.status
        locked.status = to_status
        locked.version += 1
        locked.updated_by = actor
        locked.save(update_fields=['status', 'version', 'updated_by', 'updated_at'])

        OrderStatusHistory.objects.create(
            order=locked,
            from_status=from_status,
            to_status=to_status,
            changed_by=actor,
            comment=comment,
        )
        TrackingService.record(order=locked, status=to_status, employee=actor, comment=comment)
        events.publish(
            f'order.{to_status}',
            {
                'actor_id': str(actor.id),
                'model': 'Order',
                'object_id': str(locked.id),
                'action': f'status_{to_status}',
                'old': {'status': from_status},
                'new': {'status': to_status, 'comment': comment},
            },
            source='orders',
        )
        order.status = locked.status
        order.version = locked.version
        return locked

    @staticmethod
    def history(order: Order):
        return order.status_history.select_related('changed_by').all()
