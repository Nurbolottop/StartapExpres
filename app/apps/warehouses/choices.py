from django.db import models


class ZoneType(models.TextChoices):
    """Типы зон склада (ТЗ, разделы 02, 08)."""

    RECEIVING = 'receiving', 'Приёмка'
    STORAGE = 'storage', 'Хранение'
    DISPATCH = 'dispatch', 'Отгрузка'
    RETURN = 'return', 'Возвраты'
    DAMAGED = 'damaged', 'Повреждённые'
    ARCHIVE = 'archive', 'Архив'
