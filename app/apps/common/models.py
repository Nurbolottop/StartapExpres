import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(is_deleted=True, deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class ActiveManager(models.Manager):
    """Менеджер по умолчанию: скрывает soft-deleted записи."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class AllObjectsManager(models.Manager):
    """Менеджер без фильтрации: возвращает все записи, включая удалённые."""

    def get_queryset(self) -> SoftDeleteQuerySet:
        return SoftDeleteQuerySet(self.model, using=self._db)


class BaseModel(models.Model):
    """Базовый класс всех доменных моделей (ТЗ, раздел 02).

    UUID PK, метки времени, авторство изменений, флаги активности
    и мягкого удаления. Физическое удаление — только hard_delete().
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField('Создано', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Создал',
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Обновил',
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
    )
    is_active = models.BooleanField('Активен', default=True)
    is_deleted = models.BooleanField('Удалён', default=False, editable=False)
    deleted_at = models.DateTimeField('Удалено', null=True, blank=True, editable=False)

    objects = ActiveManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Soft Delete (ТЗ, раздел 15). Физическое удаление — hard_delete()."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)


class NumberSequence(models.Model):
    """Счётчик человекочитаемых номеров (ORD-2026-000001) на префикс+год."""

    scope = models.CharField('Область', max_length=32, unique=True)
    last_value = models.PositiveBigIntegerField('Последнее значение', default=0)

    class Meta:
        verbose_name = 'Последовательность номеров'
        verbose_name_plural = 'Последовательности номеров'

    def __str__(self) -> str:
        return f'{self.scope}: {self.last_value}'
