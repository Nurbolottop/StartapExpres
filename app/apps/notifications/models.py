from django.conf import settings
from django.db import models

from apps.common.models import BaseModel
from apps.notifications.choices import (
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from apps.users.choices import Languages


class NotificationTemplate(BaseModel):
    """Шаблон уведомления в БД (ТЗ, раздел 12): никаких строк в коде.

    Переменные: {{client}}, {{order}}, {{shipment}}, {{branch}}, {{price}},
    {{driver}}, {{vehicle}}.
    """

    name = models.CharField('Название (ключ события)', max_length=100)
    type = models.CharField('Канал', max_length=20, choices=NotificationType.choices)
    language = models.CharField('Язык', max_length=2, choices=Languages.choices, default=Languages.RUSSIAN)
    title = models.CharField('Заголовок', max_length=255)
    body = models.TextField('Шаблон текста')

    class Meta:
        verbose_name = 'Шаблон уведомления'
        verbose_name_plural = 'Шаблоны уведомлений'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'type', 'language'], name='unique_template_per_channel_language'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.name} [{self.type}/{self.language}]'


class Notification(BaseModel):
    """Уведомление (ТЗ, разделы 02, 12)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Получатель',
        related_name='notifications',
        on_delete=models.CASCADE,
    )
    title = models.CharField('Заголовок', max_length=255)
    body = models.TextField('Текст')
    type = models.CharField(
        'Канал', max_length=20, choices=NotificationType.choices, default=NotificationType.IN_APP
    )
    priority = models.CharField(
        'Приоритет', max_length=10, choices=NotificationPriority.choices, default=NotificationPriority.NORMAL
    )
    status = models.CharField(
        'Статус', max_length=20, choices=NotificationStatus.choices, default=NotificationStatus.PENDING
    )
    event_type = models.CharField('Событие-источник', max_length=100, blank=True)
    is_read = models.BooleanField('Прочитано', default=False)
    sent_at = models.DateTimeField('Отправлено', null=True, blank=True)
    retry_count = models.PositiveSmallIntegerField('Попыток', default=0)
    last_error = models.CharField('Последняя ошибка', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        return f'{self.title} → {self.user_id}'
