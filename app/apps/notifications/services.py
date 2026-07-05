"""Сервисный слой notifications (ТЗ, раздел 12).

Уведомления создаются подписчиком Event Bus и отправляются только через
Celery (никогда из View). Текст — из шаблонов в БД. Повторы: 1/5/15/60 мин.
"""

import logging

from django.db import transaction
from django.utils import timezone

from apps.notifications.choices import (
    NotificationPriority,
    NotificationStatus,
    NotificationType,
)
from apps.notifications.models import Notification, NotificationTemplate

logger = logging.getLogger('notifications')


def render_template(template: str, context: dict) -> str:
    """Подстановка переменных вида {{order}} (ТЗ, раздел 12)."""
    result = template
    for key, value in context.items():
        result = result.replace('{{' + key + '}}', str(value))
    return result


class NotificationService:
    @staticmethod
    def create(
        *,
        user,
        event_type: str,
        context: dict,
        priority: str = NotificationPriority.NORMAL,
        channels: tuple = (NotificationType.IN_APP,),
    ) -> list[Notification]:
        """Создаёт уведомления по шаблонам события для каждого канала.

        Без шаблона в БД канал пропускается — текстов в коде нет (ТЗ, раздел 12).
        """
        from apps.notifications.tasks import deliver_notification

        notifications = []
        for channel in channels:
            template = (
                NotificationTemplate.objects.filter(
                    name=event_type, type=channel, language=user.language, is_active=True
                ).first()
                or NotificationTemplate.objects.filter(name=event_type, type=channel, is_active=True).first()
            )
            if template is None:
                continue
            notification = Notification.objects.create(
                user=user,
                title=render_template(template.title, context),
                body=render_template(template.body, context),
                type=channel,
                priority=priority,
                event_type=event_type,
                status=NotificationStatus.QUEUED,
            )
            notifications.append(notification)
            transaction.on_commit(
                lambda notification_id=notification.id: deliver_notification.delay(str(notification_id))
            )
        return notifications

    @staticmethod
    def mark_read(*, user, notification: Notification) -> Notification:
        notification.is_read = True
        notification.status = NotificationStatus.READ
        notification.updated_by = user
        notification.save(update_fields=['is_read', 'status', 'updated_by', 'updated_at'])
        return notification

    @staticmethod
    def deliver(notification: Notification) -> None:
        """Фактическая отправка через Provider Interface (вызывается из Celery)."""
        from apps.integrations.providers import get_provider

        if notification.type == NotificationType.IN_APP:
            notification.status = NotificationStatus.DELIVERED
            notification.sent_at = timezone.now()
            notification.save(update_fields=['status', 'sent_at', 'updated_at'])
            return

        recipient = (
            notification.user.email
            if notification.type == NotificationType.EMAIL
            else notification.user.phone
        )
        provider = get_provider(notification.type)
        provider.send(recipient=recipient or '', title=notification.title, body=notification.body)
        notification.status = NotificationStatus.SENT
        notification.sent_at = timezone.now()
        notification.save(update_fields=['status', 'sent_at', 'updated_at'])
