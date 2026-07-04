import uuid
from pathlib import Path

from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.shipments.choices import IncidentType, ShipmentStatus


def incident_photo_path(instance, filename: str) -> str:
    return f'damage/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class Shipment(BaseModel):
    """Рейс — контейнер перевозки (ТЗ, раздел 09).

    Один автомобиль, один водитель, один маршрут, множество заказов.
    Статус меняется только через ShipmentTransitionService.
    """

    shipment_number = models.CharField('Номер рейса', max_length=20, unique=True, editable=False)
    vehicle = models.ForeignKey(
        'vehicles.Vehicle',
        verbose_name='Автомобиль',
        related_name='shipments',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Водитель',
        related_name='shipments',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    route = models.ForeignKey(
        'routes.Route',
        verbose_name='Маршрут',
        related_name='shipments',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    departure_branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал отправления',
        related_name='shipments_out',
        on_delete=models.PROTECT,
    )
    arrival_branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал прибытия',
        related_name='shipments_in',
        on_delete=models.PROTECT,
    )
    planned_departure = models.DateTimeField('План отправления', null=True, blank=True)
    departure_time = models.DateTimeField('Фактическое отправление', null=True, blank=True)
    arrival_time = models.DateTimeField('Фактическое прибытие', null=True, blank=True)
    status = models.CharField(
        'Статус', max_length=20, choices=ShipmentStatus.choices, default=ShipmentStatus.DRAFT
    )
    version = models.PositiveIntegerField('Версия', default=1, editable=False)

    class Meta:
        verbose_name = 'Рейс'
        verbose_name_plural = 'Рейсы'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['driver', 'status']),
            models.Index(fields=['vehicle', 'status']),
            models.Index(fields=['departure_branch', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.shipment_number} ({self.get_status_display()})'


class ShipmentItem(BaseModel):
    """Груз в рейсе (ТЗ, раздел 02: ShipmentItem)."""

    shipment = models.ForeignKey(
        Shipment, verbose_name='Рейс', related_name='items', on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        'orders.Order',
        verbose_name='Заказ',
        related_name='shipment_items',
        on_delete=models.PROTECT,
    )
    package = models.ForeignKey(
        'packages.Package',
        verbose_name='Груз',
        related_name='shipment_items',
        on_delete=models.PROTECT,
    )
    loaded_at = models.DateTimeField('Погружен', null=True, blank=True)
    unloaded_at = models.DateTimeField('Разгружен', null=True, blank=True)

    class Meta:
        verbose_name = 'Груз рейса'
        verbose_name_plural = 'Грузы рейса'
        ordering = ('created_at',)
        constraints = [
            models.UniqueConstraint(fields=['shipment', 'package'], name='unique_package_per_shipment'),
        ]
        indexes = [models.Index(fields=['shipment', 'order'])]

    def __str__(self) -> str:
        return f'{self.shipment.shipment_number}: {self.package_id}'


class ShipmentStatusHistory(models.Model):
    """История статусов рейса. Append-only."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(
        Shipment, verbose_name='Рейс', related_name='status_history', on_delete=models.CASCADE
    )
    from_status = models.CharField('Из статуса', max_length=20, blank=True)
    to_status = models.CharField('В статус', max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Кто изменил',
        related_name='shipment_status_changes',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Когда', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'История статуса рейса'
        verbose_name_plural = 'История статусов рейсов'
        ordering = ('created_at',)

    def __str__(self) -> str:
        return f'{self.shipment_id}: {self.from_status} → {self.to_status}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('История статусов неизменяема (append-only).')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Историю статусов нельзя удалять.')


class Incident(BaseModel):
    """Инцидент рейса (ТЗ, раздел 09)."""

    shipment = models.ForeignKey(
        Shipment, verbose_name='Рейс', related_name='incidents', on_delete=models.PROTECT
    )
    type = models.CharField('Тип', max_length=20, choices=IncidentType.choices)
    description = models.TextField('Описание')
    photo = models.ImageField('Фото', upload_to=incident_photo_path, null=True, blank=True)
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'Инцидент'
        verbose_name_plural = 'Инциденты'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['shipment', 'type'])]

    def __str__(self) -> str:
        return f'{self.get_type_display()} ({self.shipment.shipment_number})'
