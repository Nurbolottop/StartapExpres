from django.db import models


class GeofenceType(models.TextChoices):
    """Типы геозон (ТЗ, раздел 10)."""

    WAREHOUSE = 'warehouse', 'Склад'
    BRANCH = 'branch', 'Филиал'
    CHECKPOINT = 'checkpoint', 'Контрольная точка'
    DELIVERY = 'delivery', 'Зона доставки'
    CUSTOM = 'custom', 'Произвольная'


class GPSEventType(models.TextChoices):
    """Типы GPS-событий (ТЗ, раздел 10)."""

    STOP = 'stop', 'Остановка'
    LONG_STOP = 'long_stop', 'Долгая остановка'
    ENTER_GEOFENCE = 'enter_geofence', 'Вход в геозону'
    EXIT_GEOFENCE = 'exit_geofence', 'Выход из геозоны'
    ROUTE_DEVIATION = 'route_deviation', 'Отклонение от маршрута'
    OVERSPEED = 'overspeed', 'Превышение скорости'
    OFFLINE = 'offline', 'Потеря связи'
