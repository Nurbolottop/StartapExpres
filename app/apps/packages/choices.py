from django.db import models


class PackageStatus(models.TextChoices):
    """FSM грузового места (ТЗ, раздел 23: PACKAGE FSM)."""

    CREATED = 'created', 'Создан'
    RECEIVED = 'received', 'Принят'
    CHECKED = 'checked', 'Проверен'
    STORED = 'stored', 'Размещён'
    WAITING_LOADING = 'waiting_loading', 'Ожидает погрузки'
    LOADED = 'loaded', 'Погружен'
    IN_TRANSIT = 'in_transit', 'В пути'
    UNLOADED = 'unloaded', 'Разгружен'
    READY_FOR_PICKUP = 'ready_for_pickup', 'Готов к выдаче'
    DELIVERED = 'delivered', 'Выдан'
    RETURNED = 'returned', 'Возврат'
    DAMAGED = 'damaged', 'Повреждён'
    LOST = 'lost', 'Утерян'


class PhotoType(models.TextChoices):
    """Этапы обязательной фотофиксации (ТЗ, разделы 04, 08)."""

    RECEIVING = 'receiving', 'Приём'
    LOADING = 'loading', 'Погрузка'
    UNLOADING = 'unloading', 'Разгрузка'
    DELIVERY = 'delivery', 'Выдача'
    DAMAGE = 'damage', 'Повреждение'
