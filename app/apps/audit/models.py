import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Журнал действий (ТЗ, разделы 02, 12, 17). Append-only:
    записи нельзя изменять и удалять, хранение — минимум 5 лет."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        related_name='audit_logs',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    role = models.CharField('Роль', max_length=20, blank=True)
    model = models.CharField('Модель', max_length=100)
    object_uuid = models.CharField('ID объекта', max_length=64, blank=True)
    action = models.CharField('Действие', max_length=50)
    event_type = models.CharField('Тип события', max_length=100, blank=True)
    old_data = models.JSONField('Старые данные', default=dict, blank=True)
    new_data = models.JSONField('Новые данные', default=dict, blank=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=512, blank=True)
    request_id = models.CharField('Request ID', max_length=64, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'Запись аудита'
        verbose_name_plural = 'Журнал аудита'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['model', 'object_uuid']),
            models.Index(fields=['action']),
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.action} {self.model} ({self.created_at:%Y-%m-%d %H:%M})'

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError('Записи аудита неизменяемы (append-only).')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError('Записи аудита нельзя удалять.')
