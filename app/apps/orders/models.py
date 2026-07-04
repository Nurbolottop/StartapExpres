import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import phone_validator
from apps.orders.choices import DeliveryType, OrderStatus, PaymentType


class Order(BaseModel):
    """Заказ — центральная сущность системы (ТЗ, раздел 07).

    Статус изменяется только через OrderTransitionService.
    Физическое удаление запрещено (только Soft Delete).
    """

    order_number = models.CharField('Номер заказа', max_length=20, unique=True, editable=False)
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Клиент',
        related_name='orders',
        on_delete=models.PROTECT,
    )

    sender_name = models.CharField('Отправитель', max_length=255)
    sender_phone = models.CharField('Телефон отправителя', max_length=16, validators=[phone_validator])
    sender_address = models.CharField('Адрес отправителя', max_length=255, blank=True)
    receiver_name = models.CharField('Получатель', max_length=255)
    receiver_phone = models.CharField('Телефон получателя', max_length=16, validators=[phone_validator])
    receiver_address = models.CharField('Адрес получателя', max_length=255, blank=True)

    from_branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал отправления',
        related_name='orders_from',
        on_delete=models.PROTECT,
    )
    to_branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал назначения',
        related_name='orders_to',
        on_delete=models.PROTECT,
    )

    payment_type = models.CharField(
        'Способ оплаты', max_length=20, choices=PaymentType.choices, default=PaymentType.CASH
    )
    delivery_type = models.CharField(
        'Тип доставки', max_length=20, choices=DeliveryType.choices, default=DeliveryType.BRANCH_PICKUP
    )
    tariff = models.ForeignKey(
        'tariffs.Tariff',
        verbose_name='Тариф',
        related_name='orders',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    total_price = models.DecimalField(
        'Стоимость', max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    insurance_price = models.DecimalField(
        'Страховка', max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    paid_amount = models.DecimalField(
        'Оплачено', max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    price_details = models.JSONField('Разбивка стоимости', default=dict, blank=True)

    status = models.CharField('Статус', max_length=25, choices=OrderStatus.choices, default=OrderStatus.DRAFT)
    comment = models.TextField('Комментарий', blank=True)
    version = models.PositiveIntegerField('Версия', default=1, editable=False)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['client', 'status']),
            models.Index(fields=['from_branch', 'status']),
            models.Index(fields=['to_branch', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.order_number} ({self.get_status_display()})'


class OrderServiceItem(BaseModel):
    """Дополнительная услуга заказа с зафиксированной ценой (ТЗ, раздел 07)."""

    order = models.ForeignKey(
        Order, verbose_name='Заказ', related_name='service_items', on_delete=models.CASCADE
    )
    service = models.ForeignKey(
        'tariffs.AdditionalService',
        verbose_name='Услуга',
        related_name='order_items',
        on_delete=models.PROTECT,
    )
    price = models.DecimalField(
        'Цена на момент заказа', max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = 'Услуга заказа'
        verbose_name_plural = 'Услуги заказа'
        ordering = ('created_at',)
        constraints = [
            models.UniqueConstraint(fields=['order', 'service'], name='unique_service_per_order'),
        ]

    def __str__(self) -> str:
        return f'{self.order.order_number}: {self.service.name}'


class OrderStatusHistory(models.Model):
    """История статусов заказа (ТЗ, разделы 07, 23). Append-only."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        Order, verbose_name='Заказ', related_name='status_history', on_delete=models.CASCADE
    )
    from_status = models.CharField('Из статуса', max_length=25, blank=True)
    to_status = models.CharField('В статус', max_length=25)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Кто изменил',
        related_name='order_status_changes',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField('Когда', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'История статуса заказа'
        verbose_name_plural = 'История статусов заказов'
        ordering = ('created_at',)
        indexes = [models.Index(fields=['order', 'created_at'])]

    def __str__(self) -> str:
        return f'{self.order_id}: {self.from_status} → {self.to_status}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('История статусов неизменяема (append-only).')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Историю статусов нельзя удалять.')
