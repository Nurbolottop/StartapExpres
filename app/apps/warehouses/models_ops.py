"""Операционные модели склада (ТЗ, раздел 08): перемещения, инвентаризация,
акты повреждения/утери, подтверждение выдачи."""

from django.db import models

from apps.common.models import BaseModel


class WarehouseMovement(BaseModel):
    """Перемещение груза между ячейками (ТЗ, раздел 08). Историю удалять нельзя."""

    package = models.ForeignKey(
        'packages.Package', verbose_name='Груз', related_name='movements', on_delete=models.PROTECT
    )
    from_cell = models.ForeignKey(
        'warehouses.WarehouseCell',
        verbose_name='Откуда',
        related_name='movements_from',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    to_cell = models.ForeignKey(
        'warehouses.WarehouseCell',
        verbose_name='Куда',
        related_name='movements_to',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    reason = models.CharField('Причина', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Перемещение груза'
        verbose_name_plural = 'Перемещения грузов'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['package', 'created_at'])]

    def __str__(self) -> str:
        return f'{self.package_id}: {self.from_cell_id or "-"} → {self.to_cell_id or "-"}'


class DamageReport(BaseModel):
    """Акт повреждения груза (ТЗ, разделы 04, 08)."""

    package = models.ForeignKey(
        'packages.Package',
        verbose_name='Груз',
        related_name='damage_reports',
        on_delete=models.PROTECT,
    )
    description = models.TextField('Описание повреждения')
    reason = models.CharField('Причина', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Акт повреждения'
        verbose_name_plural = 'Акты повреждений'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Повреждение {self.package_id}'


class LostReport(BaseModel):
    """Акт утери груза (ТЗ, разделы 04, 08). Запускает расследование."""

    package = models.ForeignKey(
        'packages.Package',
        verbose_name='Груз',
        related_name='lost_reports',
        on_delete=models.PROTECT,
    )
    description = models.TextField('Обстоятельства')

    class Meta:
        verbose_name = 'Акт утери'
        verbose_name_plural = 'Акты утери'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Утеря {self.package_id}'


class InventorySession(BaseModel):
    """Сессия инвентаризации склада (ТЗ, раздел 08)."""

    warehouse = models.ForeignKey(
        'warehouses.Warehouse',
        verbose_name='Склад',
        related_name='inventory_sessions',
        on_delete=models.PROTECT,
    )
    finished_at = models.DateTimeField('Завершена', null=True, blank=True)
    report = models.JSONField('Отчёт', default=dict, blank=True)

    class Meta:
        verbose_name = 'Инвентаризация'
        verbose_name_plural = 'Инвентаризации'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        state = 'завершена' if self.finished_at else 'идёт'
        return f'Инвентаризация {self.warehouse_id} ({state})'


class InventoryScan(BaseModel):
    """Скан груза в рамках инвентаризации."""

    session = models.ForeignKey(
        InventorySession, verbose_name='Сессия', related_name='scans', on_delete=models.CASCADE
    )
    package = models.ForeignKey(
        'packages.Package',
        verbose_name='Груз',
        related_name='inventory_scans',
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = 'Скан инвентаризации'
        verbose_name_plural = 'Сканы инвентаризации'
        ordering = ('created_at',)
        constraints = [
            models.UniqueConstraint(fields=['session', 'package'], name='unique_scan_per_session'),
        ]

    def __str__(self) -> str:
        return f'{self.session_id}: {self.package_id}'


class DeliveryConfirmation(BaseModel):
    """Подтверждение выдачи заказа (ТЗ, разделы 04, 08): получатель,
    документ, подпись."""

    order = models.OneToOneField(
        'orders.Order',
        verbose_name='Заказ',
        related_name='delivery_confirmation',
        on_delete=models.PROTECT,
    )
    received_by_name = models.CharField('Кто получил', max_length=255)
    document_number = models.CharField('Документ', max_length=100)
    signature = models.ImageField('Подпись', upload_to='documents/signatures/', null=True, blank=True)

    class Meta:
        verbose_name = 'Подтверждение выдачи'
        verbose_name_plural = 'Подтверждения выдачи'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Выдача {self.order_id} — {self.received_by_name}'
