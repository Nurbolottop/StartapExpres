import uuid

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.gps.choices import GeofenceType, GPSEventType


class GPSLog(models.Model):
    """Точка GPS (ТЗ, разделы 02, 10). Immutable; записей — миллионы;
    партиционирование по месяцам — при переходе на прод (раздел 26)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        verbose_name='Автомобиль',
        related_name='gps_logs',
        on_delete=models.CASCADE,
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Водитель',
        related_name='gps_logs',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    shipment = models.ForeignKey(
        'shipments.Shipment',
        verbose_name='Рейс',
        related_name='gps_logs',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6)
    altitude = models.DecimalField('Высота, м', max_digits=7, decimal_places=1, null=True, blank=True)
    speed = models.DecimalField('Скорость, км/ч', max_digits=5, decimal_places=1, default=0)
    heading = models.PositiveSmallIntegerField('Курс, °', null=True, blank=True)
    accuracy = models.DecimalField('Погрешность, м', max_digits=6, decimal_places=1, default=0)
    battery_level = models.PositiveSmallIntegerField('Заряд, %', null=True, blank=True)
    device_id = models.CharField('Device ID', max_length=64, blank=True)
    app_version = models.CharField('Версия приложения', max_length=20, blank=True)
    device_time = models.DateTimeField('Время устройства')
    server_time = models.DateTimeField('Время сервера', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'GPS-точка'
        verbose_name_plural = 'GPS-журнал'
        ordering = ('-server_time',)
        indexes = [
            models.Index(fields=['vehicle', 'server_time']),
            models.Index(fields=['shipment', 'server_time']),
            models.Index(fields=['driver', 'server_time']),
        ]

    def __str__(self) -> str:
        return f'{self.vehicle_id} @ {self.latitude},{self.longitude}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('GPS-история неизменяема (append-only).')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('GPS-историю нельзя удалять вручную.')


class Geofence(BaseModel):
    """Геозона (ТЗ, раздел 10)."""

    name = models.CharField('Название', max_length=150)
    type = models.CharField('Тип', max_length=20, choices=GeofenceType.choices, default=GeofenceType.CUSTOM)
    latitude = models.DecimalField('Широта центра', max_digits=9, decimal_places=6)
    longitude = models.DecimalField('Долгота центра', max_digits=9, decimal_places=6)
    radius_m = models.PositiveIntegerField('Радиус, м', default=500)

    class Meta:
        verbose_name = 'Геозона'
        verbose_name_plural = 'Геозоны'
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} ({self.get_type_display()})'


class GPSEvent(models.Model):
    """Событие GPS-мониторинга (ТЗ, раздел 10). Immutable."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        verbose_name='Автомобиль',
        related_name='gps_events',
        on_delete=models.CASCADE,
    )
    shipment = models.ForeignKey(
        'shipments.Shipment',
        verbose_name='Рейс',
        related_name='gps_events',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    type = models.CharField('Тип', max_length=20, choices=GPSEventType.choices)
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)
    details = models.JSONField('Детали', default=dict, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'GPS-событие'
        verbose_name_plural = 'GPS-события'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['vehicle', 'type']),
            models.Index(fields=['shipment', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.get_type_display()} ({self.vehicle_id})'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('GPS-события неизменяемы (append-only).')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('GPS-события нельзя удалять.')
