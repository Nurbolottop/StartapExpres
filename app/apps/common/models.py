import uuid

from django.db import models
from django.utils import timezone


class UUIDModel(models.Model):
    """UUID вместо автоинкремента: безопасные внешние идентификаторы,
    независимость от БД при шардировании/слиянии данных филиалов."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField('Создано', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Базовый класс всех доменных моделей системы."""

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    def __init__(self, *args, alive_only=True, **kwargs):
        self.alive_only = alive_only
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = SoftDeleteQuerySet(self.model, using=self._db)
        return queryset.alive() if self.alive_only else queryset


class SoftDeleteModel(models.Model):
    """Мягкое удаление: записи с историей (заказы, платежи) физически не удаляются.

    `objects` скрывает удалённые записи, `all_objects` возвращает все.
    """

    deleted_at = models.DateTimeField('Удалено', null=True, blank=True, editable=False)

    objects = SoftDeleteManager()
    all_objects = SoftDeleteManager(alive_only=False)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
