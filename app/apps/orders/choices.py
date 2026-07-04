"""Статусная модель заказа (ТЗ, разделы 07, 23)."""

from django.db import models

from apps.users.choices import Roles


class OrderStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    WAITING_CONFIRMATION = 'waiting_confirmation', 'Ожидает подтверждения'
    NEED_CORRECTION = 'need_correction', 'Требует исправления'
    CONFIRMED = 'confirmed', 'Подтверждён'
    WAITING_PAYMENT = 'waiting_payment', 'Ожидает оплаты'
    PARTIALLY_PAID = 'partially_paid', 'Частично оплачен'
    PAID = 'paid', 'Оплачен'
    WAITING_RECEIVE = 'waiting_receive', 'Ожидает приёма груза'
    RECEIVED = 'received', 'Груз принят'
    IN_WAREHOUSE = 'in_warehouse', 'На складе'
    WAITING_SHIPMENT = 'waiting_shipment', 'Ожидает рейса'
    LOADED = 'loaded', 'Погружен'
    IN_TRANSIT = 'in_transit', 'В пути'
    ARRIVED = 'arrived', 'Прибыл'
    READY_FOR_PICKUP = 'ready_for_pickup', 'Готов к выдаче'
    DELIVERED = 'delivered', 'Выдан получателю'
    COMPLETED = 'completed', 'Завершён'
    CANCELLED = 'cancelled', 'Отменён'
    RETURNED = 'returned', 'Возврат'
    DAMAGED = 'damaged', 'Повреждён'
    LOST = 'lost', 'Утерян'


class PaymentType(models.TextChoices):
    CASH = 'cash', 'Наличные'
    CARD = 'card', 'Карта'
    QR = 'qr', 'QR-оплата'
    BANK_TRANSFER = 'bank_transfer', 'Банковский перевод'
    POST_PAYMENT = 'post_payment', 'Постоплата'


class DeliveryType(models.TextChoices):
    BRANCH_PICKUP = 'branch_pickup', 'Выдача в филиале'
    DOOR_DELIVERY = 'door_delivery', 'Доставка до двери'


# Статусы, до которых (включительно) заказ можно редактировать целиком
EDITABLE_STATUSES = frozenset(
    {
        OrderStatus.DRAFT,
        OrderStatus.WAITING_CONFIRMATION,
        OrderStatus.NEED_CORRECTION,
    }
)

# Статусы, начиная с которых заказ считается отправленным (редактирование запрещено)
SHIPPED_STATUSES = frozenset(
    {
        OrderStatus.LOADED,
        OrderStatus.IN_TRANSIT,
        OrderStatus.ARRIVED,
        OrderStatus.READY_FOR_PICKUP,
        OrderStatus.DELIVERED,
        OrderStatus.COMPLETED,
    }
)

# Поля, замороженные после подтверждения (ТЗ, раздел 07)
FROZEN_AFTER_CONFIRM = frozenset(
    {
        'sender_name',
        'sender_phone',
        'sender_address',
        'receiver_name',
        'receiver_phone',
        'receiver_address',
        'from_branch',
        'to_branch',
        'total_price',
    }
)

# Конечный автомат (ТЗ, раздел 23) + NEED_CORRECTION (раздел 07)
STATUS_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.DRAFT: frozenset({OrderStatus.WAITING_CONFIRMATION, OrderStatus.CANCELLED}),
    OrderStatus.WAITING_CONFIRMATION: frozenset(
        {OrderStatus.CONFIRMED, OrderStatus.NEED_CORRECTION, OrderStatus.CANCELLED}
    ),
    OrderStatus.NEED_CORRECTION: frozenset({OrderStatus.WAITING_CONFIRMATION, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.WAITING_PAYMENT, OrderStatus.CANCELLED}),
    OrderStatus.WAITING_PAYMENT: frozenset(
        {OrderStatus.PARTIALLY_PAID, OrderStatus.PAID, OrderStatus.CANCELLED}
    ),
    OrderStatus.PARTIALLY_PAID: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),
    OrderStatus.PAID: frozenset({OrderStatus.WAITING_RECEIVE, OrderStatus.CANCELLED}),
    OrderStatus.WAITING_RECEIVE: frozenset({OrderStatus.RECEIVED, OrderStatus.CANCELLED}),
    OrderStatus.RECEIVED: frozenset({OrderStatus.IN_WAREHOUSE, OrderStatus.DAMAGED, OrderStatus.CANCELLED}),
    OrderStatus.IN_WAREHOUSE: frozenset(
        {OrderStatus.WAITING_SHIPMENT, OrderStatus.DAMAGED, OrderStatus.LOST, OrderStatus.CANCELLED}
    ),
    OrderStatus.WAITING_SHIPMENT: frozenset(
        {OrderStatus.LOADED, OrderStatus.DAMAGED, OrderStatus.LOST, OrderStatus.CANCELLED}
    ),
    OrderStatus.LOADED: frozenset({OrderStatus.IN_TRANSIT, OrderStatus.DAMAGED}),
    OrderStatus.IN_TRANSIT: frozenset({OrderStatus.ARRIVED, OrderStatus.DAMAGED, OrderStatus.LOST}),
    OrderStatus.ARRIVED: frozenset({OrderStatus.READY_FOR_PICKUP, OrderStatus.DAMAGED}),
    OrderStatus.READY_FOR_PICKUP: frozenset({OrderStatus.DELIVERED, OrderStatus.RETURNED}),
    OrderStatus.DELIVERED: frozenset({OrderStatus.COMPLETED, OrderStatus.RETURNED}),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.RETURNED: frozenset(),
    OrderStatus.DAMAGED: frozenset({OrderStatus.RETURNED}),
    OrderStatus.LOST: frozenset(),
}

_STAFF = frozenset({Roles.OPERATOR, Roles.DIRECTOR, Roles.SUPERADMIN})
_WAREHOUSE_STAFF = frozenset({Roles.WAREHOUSE, Roles.OPERATOR, Roles.DIRECTOR, Roles.SUPERADMIN})
_FINANCE_STAFF = frozenset({Roles.FINANCE, Roles.OPERATOR, Roles.DIRECTOR, Roles.SUPERADMIN})
_TRANSPORT = frozenset({Roles.DRIVER, Roles.WAREHOUSE, Roles.OPERATOR, Roles.DIRECTOR, Roles.SUPERADMIN})

# Какие роли могут переводить заказ В статус (ТЗ, разделы 07, 14, 23)
TRANSITION_ALLOWED_ROLES: dict[str, frozenset[str]] = {
    OrderStatus.WAITING_CONFIRMATION: frozenset({Roles.CLIENT}) | _STAFF,
    OrderStatus.NEED_CORRECTION: _STAFF,
    OrderStatus.CONFIRMED: _STAFF,
    OrderStatus.WAITING_PAYMENT: _STAFF,
    OrderStatus.PARTIALLY_PAID: _FINANCE_STAFF,
    OrderStatus.PAID: _FINANCE_STAFF,
    OrderStatus.WAITING_RECEIVE: _FINANCE_STAFF,
    OrderStatus.RECEIVED: _WAREHOUSE_STAFF,
    OrderStatus.IN_WAREHOUSE: _WAREHOUSE_STAFF,
    OrderStatus.WAITING_SHIPMENT: _WAREHOUSE_STAFF,
    OrderStatus.LOADED: _WAREHOUSE_STAFF,
    OrderStatus.IN_TRANSIT: _TRANSPORT,
    OrderStatus.ARRIVED: _TRANSPORT,
    OrderStatus.READY_FOR_PICKUP: _WAREHOUSE_STAFF,
    OrderStatus.DELIVERED: _WAREHOUSE_STAFF,
    OrderStatus.COMPLETED: _FINANCE_STAFF,
    OrderStatus.CANCELLED: frozenset({Roles.CLIENT}) | _STAFF,
    OrderStatus.RETURNED: _WAREHOUSE_STAFF,
    OrderStatus.DAMAGED: _WAREHOUSE_STAFF,
    OrderStatus.LOST: _WAREHOUSE_STAFF,
}

# Статусы, в которых клиент ещё может отменить свой заказ (ТЗ, разделы 04, 07)
CLIENT_CANCELLABLE_STATUSES = frozenset(
    {
        OrderStatus.DRAFT,
        OrderStatus.WAITING_CONFIRMATION,
        OrderStatus.NEED_CORRECTION,
    }
)
