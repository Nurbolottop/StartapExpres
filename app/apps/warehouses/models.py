from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import phone_validator
from apps.warehouses.choices import ZoneType


class Warehouse(BaseModel):
    """Склад филиала (ТЗ, раздел 02: WAREHOUSE)."""

    branch = models.ForeignKey(
        'branches.Branch', verbose_name='Филиал', related_name='warehouses', on_delete=models.PROTECT
    )
    name = models.CharField('Название', max_length=150)
    code = models.CharField('Код', max_length=20, unique=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Заведующий',
        related_name='managed_warehouses',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    phone = models.CharField('Телефон', max_length=16, blank=True, validators=[phone_validator])
    total_area = models.DecimalField(
        'Площадь, м²',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    max_weight = models.DecimalField(
        'Макс. вес, кг',
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'
        ordering = ('name',)
        indexes = [models.Index(fields=['branch'])]

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'


class WarehouseZone(BaseModel):
    """Зона склада (ТЗ, разделы 02, 08)."""

    warehouse = models.ForeignKey(
        Warehouse, verbose_name='Склад', related_name='zones', on_delete=models.PROTECT
    )
    name = models.CharField('Название', max_length=150)
    code = models.CharField('Код', max_length=20)
    type = models.CharField('Тип', max_length=20, choices=ZoneType.choices, default=ZoneType.STORAGE)

    class Meta:
        verbose_name = 'Зона склада'
        verbose_name_plural = 'Зоны склада'
        ordering = ('warehouse', 'code')
        constraints = [
            models.UniqueConstraint(fields=['warehouse', 'code'], name='unique_zone_code_per_warehouse'),
        ]
        indexes = [models.Index(fields=['warehouse', 'type'])]

    def __str__(self) -> str:
        return f'{self.warehouse.code} / {self.code} ({self.get_type_display()})'


class WarehouseCell(BaseModel):
    """Ячейка склада с контролем вместимости (ТЗ, разделы 02, 08, 22)."""

    zone = models.ForeignKey(
        WarehouseZone, verbose_name='Зона', related_name='cells', on_delete=models.PROTECT
    )
    code = models.CharField('Код', max_length=20)
    shelf = models.CharField('Стеллаж', max_length=20, blank=True)
    row = models.CharField('Ряд', max_length=20, blank=True)
    level = models.CharField('Полка/уровень', max_length=20, blank=True)
    capacity_weight = models.DecimalField(
        'Вместимость, кг', max_digits=10, decimal_places=2, validators=[MinValueValidator(0)]
    )
    capacity_volume = models.DecimalField(
        'Вместимость, м³', max_digits=10, decimal_places=3, validators=[MinValueValidator(0)]
    )
    occupied_weight = models.DecimalField('Занято, кг', max_digits=10, decimal_places=2, default=0)
    occupied_volume = models.DecimalField('Занято, м³', max_digits=10, decimal_places=3, default=0)

    class Meta:
        verbose_name = 'Ячейка склада'
        verbose_name_plural = 'Ячейки склада'
        ordering = ('zone', 'code')
        constraints = [
            models.UniqueConstraint(fields=['zone', 'code'], name='unique_cell_code_per_zone'),
            models.CheckConstraint(
                condition=models.Q(occupied_weight__lte=models.F('capacity_weight')),
                name='cell_weight_within_capacity',
            ),
            models.CheckConstraint(
                condition=models.Q(occupied_volume__lte=models.F('capacity_volume')),
                name='cell_volume_within_capacity',
            ),
        ]
        indexes = [models.Index(fields=['zone'])]

    def __str__(self) -> str:
        return f'{self.zone} / {self.code}'

    @property
    def free_weight(self):
        return self.capacity_weight - self.occupied_weight

    @property
    def free_volume(self):
        return self.capacity_volume - self.occupied_volume

    def fits(self, weight, volume) -> bool:
        return weight <= self.free_weight and volume <= self.free_volume
