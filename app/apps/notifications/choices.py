from django.db import models


class NotificationType(models.TextChoices):
    PUSH = 'push', 'Push'
    SMS = 'sms', 'SMS'
    EMAIL = 'email', 'Email'
    TELEGRAM = 'telegram', 'Telegram'
    IN_APP = 'in_app', 'In-App'


class NotificationStatus(models.TextChoices):
    PENDING = 'pending', 'Ожидает'
    QUEUED = 'queued', 'В очереди'
    SENDING = 'sending', 'Отправляется'
    SENT = 'sent', 'Отправлено'
    DELIVERED = 'delivered', 'Доставлено'
    READ = 'read', 'Прочитано'
    FAILED = 'failed', 'Ошибка'
    CANCELLED = 'cancelled', 'Отменено'


class DevicePlatform(models.TextChoices):
    ANDROID = 'android', 'Android'
    IOS = 'ios', 'iOS'


class NotificationPriority(models.TextChoices):
    LOW = 'low', 'Низкий'
    NORMAL = 'normal', 'Обычный'
    HIGH = 'high', 'Высокий'
    CRITICAL = 'critical', 'Критический'


# Повторы отправки (ТЗ, раздел 12): 1, 5, 15, 60 минут
RETRY_DELAYS_MINUTES = (1, 5, 15, 60)
