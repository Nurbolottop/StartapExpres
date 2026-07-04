from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.vehicles.choices import FuelType, VehicleStatus


class VehicleType(BaseModel):
    """Тип автомобиля (ТЗ, раздел 02: VEHICLES)."""

    name = models.CharField('Название', max_length=100)
    code = models.CharField('Код', max_length=20, unique=True)
    max_weight = models.DecimalField(
        'Макс. вес, кг', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    max_volume = models.DecimalField(
        'Макс. объём, м³', max_digits=10, decimal_places=3, validators=[MinValueValidator(0)]
    )
    axle_count = models.PositiveSmallIntegerField('Количество осей', default=2)

    class Meta:
        verbose_name = 'Тип автомобиля'
        verbose_name_plural = 'Типы автомобилей'
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'


class Vehicle(BaseModel):
    """Автомобиль (ТЗ, раздел 02: VEHICLES)."""

    vehicle_type = models.ForeignKey(
        VehicleType, verbose_name='Тип', related_name='vehicles', on_delete=models.PROTECT
    )
    branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал',
        related_name='vehicles',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    plate_number = models.CharField('Госномер', max_length=20, unique=True)
    vin = models.CharField('VIN', max_length=17, unique=True, null=True, blank=True)
    brand = models.CharField('Марка', max_length=100)
    model = models.CharField('Модель', max_length=100, blank=True)
    year = models.PositiveSmallIntegerField('Год выпуска', null=True, blank=True)
    color = models.CharField('Цвет', max_length=50, blank=True)
    max_weight = models.DecimalField(
        'Макс. вес, кг', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    max_volume = models.DecimalField(
        'Макс. объём, м³', max_digits=10, decimal_places=3, validators=[MinValueValidator(0)]
    )
    fuel_type = models.CharField('Топливо', max_length=20, choices=FuelType.choices, default=FuelType.DIESEL)
    mileage = models.PositiveIntegerField('Пробег, км', default=0)
    status = models.CharField(
        'Статус', max_length=20, choices=VehicleStatus.choices, default=VehicleStatus.AVAILABLE
    )
    current_driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Текущий водитель',
        related_name='assigned_vehicles',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ('plate_number',)
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['branch', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.brand} {self.model} ({self.plate_number})'

    def save(self, *args, **kwargs):
        self.vin = self.vin or None
        super().save(*args, **kwargs)
