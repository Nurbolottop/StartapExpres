"""Отправка уведомлений через Celery с повторами 1/5/15/60 мин (ТЗ, раздел 12)."""

import logging

from celery import shared_task

from apps.notifications.choices import RETRY_DELAYS_MINUTES, NotificationStatus

logger = logging.getLogger('notifications')


@shared_task(name='notifications.deliver', bind=True, max_retries=len(RETRY_DELAYS_MINUTES))
def deliver_notification(self, notification_id: str) -> str:
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService

    notification = Notification.objects.filter(id=notification_id).first()
    if notification is None or notification.status in (
        NotificationStatus.SENT,
        NotificationStatus.DELIVERED,
        NotificationStatus.CANCELLED,
    ):
        return 'skipped'

    notification.status = NotificationStatus.SENDING
    notification.save(update_fields=['status', 'updated_at'])
    try:
        NotificationService.deliver(notification)
        return 'sent'
    except Exception as exc:  # noqa: BLE001 — любой сбой канала уходит в retry
        notification.retry_count += 1
        notification.last_error = str(exc)[:255]
        if notification.retry_count > len(RETRY_DELAYS_MINUTES):
            notification.status = NotificationStatus.FAILED
            notification.save(update_fields=['retry_count', 'last_error', 'status', 'updated_at'])
            logger.error('Уведомление %s не доставлено: %s', notification_id, exc)
            return 'failed'
        notification.status = NotificationStatus.QUEUED
        notification.save(update_fields=['retry_count', 'last_error', 'status', 'updated_at'])
        delay = RETRY_DELAYS_MINUTES[notification.retry_count - 1] * 60
        raise self.retry(exc=exc, countdown=delay)
