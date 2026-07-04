import uuid

from django.conf import settings
from django.db import models


class TrackingEvent(models.Model):
    """Событие трекинга заказа/груза (ТЗ, разделы 02, 10). Immutable."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(
        'orders.Order',
        verbose_name='Заказ',
        related_name='tracking_events',
        on_delete=models.CASCADE,
    )
    package = models.ForeignKey(
        'packages.Package',
        verbose_name='Груз',
        related_name='tracking_events',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    status = models.CharField('Событие/статус', max_length=50)
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)
    comment = models.TextField('Комментарий', blank=True)
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Сотрудник',
        related_name='tracking_events',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField('Создано', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Событие трекинга'
        verbose_name_plural = 'События трекинга'
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['order', 'created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return f'{self.order_id}: {self.status}'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('События трекинга неизменяемы (append-only).')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('События трекинга нельзя удалять.')
