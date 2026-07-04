"""Статусная модель рейса (ТЗ, разделы 09, 22, 23)."""

from django.db import models

from apps.users.choices import Roles


class ShipmentStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    PLANNED = 'planned', 'Запланирован'
    READY = 'ready', 'Готов к погрузке'
    LOADING = 'loading', 'Погрузка'
    LOADED = 'loaded', 'Погружен'
    STARTED = 'started', 'Стартовал'
    IN_TRANSIT = 'in_transit', 'В пути'
    GPS_LOST = 'gps_lost', 'Потеря GPS'
    ARRIVED = 'arrived', 'Прибыл'
    UNLOADING = 'unloading', 'Разгрузка'
    COMPLETED = 'completed', 'Завершён'
    CANCELLED = 'cancelled', 'Отменён'
    FAILED = 'failed', 'Сорван'


class IncidentType(models.TextChoices):
    ACCIDENT = 'accident', 'ДТП'
    BREAKDOWN = 'breakdown', 'Поломка'
    DELAY = 'delay', 'Задержка'
    TRAFFIC = 'traffic', 'Пробка'
    WEATHER = 'weather', 'Плохая погода'
    DAMAGE = 'damage', 'Повреждение груза'
    LOSS = 'loss', 'Потеря груза'
    OTHER = 'other', 'Другое'


# Активные статусы: машина/водитель заняты, состав заморожен после STARTED
ACTIVE_STATUSES = frozenset(
    {
        ShipmentStatus.PLANNED,
        ShipmentStatus.READY,
        ShipmentStatus.LOADING,
        ShipmentStatus.LOADED,
        ShipmentStatus.STARTED,
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.GPS_LOST,
        ShipmentStatus.ARRIVED,
        ShipmentStatus.UNLOADING,
    }
)

# Открытые рейсы: заказ/груз не может состоять в двух таких одновременно
OPEN_STATUSES = ACTIVE_STATUSES | {ShipmentStatus.DRAFT}

STARTED_STATUSES = frozenset(
    {
        ShipmentStatus.STARTED,
        ShipmentStatus.IN_TRANSIT,
        ShipmentStatus.GPS_LOST,
        ShipmentStatus.ARRIVED,
        ShipmentStatus.UNLOADING,
    }
)

SHIPMENT_TRANSITIONS: dict[str, frozenset[str]] = {
    ShipmentStatus.DRAFT: frozenset({ShipmentStatus.PLANNED, ShipmentStatus.CANCELLED}),
    ShipmentStatus.PLANNED: frozenset({ShipmentStatus.READY, ShipmentStatus.CANCELLED}),
    ShipmentStatus.READY: frozenset({ShipmentStatus.LOADING, ShipmentStatus.CANCELLED}),
    ShipmentStatus.LOADING: frozenset({ShipmentStatus.LOADED, ShipmentStatus.CANCELLED}),
    ShipmentStatus.LOADED: frozenset({ShipmentStatus.STARTED, ShipmentStatus.CANCELLED}),
    ShipmentStatus.STARTED: frozenset({ShipmentStatus.IN_TRANSIT, ShipmentStatus.FAILED}),
    ShipmentStatus.IN_TRANSIT: frozenset(
        {ShipmentStatus.ARRIVED, ShipmentStatus.GPS_LOST, ShipmentStatus.FAILED}
    ),
    ShipmentStatus.GPS_LOST: frozenset({ShipmentStatus.IN_TRANSIT, ShipmentStatus.FAILED}),
    ShipmentStatus.ARRIVED: frozenset({ShipmentStatus.UNLOADING, ShipmentStatus.FAILED}),
    ShipmentStatus.UNLOADING: frozenset({ShipmentStatus.COMPLETED}),
    ShipmentStatus.COMPLETED: frozenset(),
    ShipmentStatus.CANCELLED: frozenset(),
    ShipmentStatus.FAILED: frozenset(),
}

_STAFF = frozenset({Roles.OPERATOR, Roles.DIRECTOR, Roles.SUPERADMIN})
_WAREHOUSE = frozenset({Roles.WAREHOUSE}) | _STAFF
_DRIVER = frozenset({Roles.DRIVER}) | _STAFF

SHIPMENT_TRANSITION_ROLES: dict[str, frozenset[str]] = {
    ShipmentStatus.PLANNED: _STAFF,
    ShipmentStatus.READY: _STAFF,
    ShipmentStatus.LOADING: _WAREHOUSE,
    ShipmentStatus.LOADED: _WAREHOUSE,
    ShipmentStatus.STARTED: _DRIVER,
    ShipmentStatus.IN_TRANSIT: _DRIVER,
    ShipmentStatus.GPS_LOST: _STAFF,
    ShipmentStatus.ARRIVED: _DRIVER,
    ShipmentStatus.UNLOADING: _WAREHOUSE,
    ShipmentStatus.COMPLETED: _WAREHOUSE,
    ShipmentStatus.CANCELLED: _STAFF,
    ShipmentStatus.FAILED: _STAFF,
}
