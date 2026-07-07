"""Provider Interface для внешних каналов (ТЗ, раздел 16).

Бизнес-код не знает о конкретном провайдере: канал → провайдер из настроек.
Смена оператора (Beeline/MegaCom/O!/Twilio, SMTP/SendGrid и т.д.) — только
регистрация нового класса, без изменения бизнес-логики.

В v1 подключён LogProvider (запись в лог) — боевые ключи операторов
подставляются на внедрении без изменения кода (см. docs/DEVIATIONS.md).
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger('notifications')


class BaseProvider(ABC):
    """Единый интерфейс провайдера канала (ТЗ, раздел 16: send/balance/status)."""

    channel = 'base'

    @abstractmethod
    def send(self, *, recipient: str, title: str, body: str) -> str:
        """Отправляет сообщение, возвращает внешний ID. Бросает исключение при сбое."""

    def status(self, external_id: str) -> str:
        return 'unknown'


class LogProvider(BaseProvider):
    """Провайдер-заглушка: пишет сообщение в лог. Используется в dev
    и как безопасный fallback до подключения боевых операторов."""

    def __init__(self, channel: str):
        self.channel = channel

    def send(self, *, recipient: str, title: str, body: str) -> str:
        logger.info('[%s] -> %s: %s | %s', self.channel, recipient, title, body)
        return f'log-{self.channel}'


class FCMProvider(BaseProvider):
    """Push через Firebase Cloud Messaging (HTTP v1, firebase-admin).

    recipient — FCM-токен устройства. Регистрируется автоматически при
    заданном FIREBASE_CREDENTIALS_FILE (см. configure_providers)."""

    channel = 'push'

    def __init__(self, credentials_file: str):
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            firebase_admin.initialize_app(credentials.Certificate(credentials_file))

    def send(self, *, recipient: str, title: str, body: str) -> str:
        from firebase_admin import messaging

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=recipient,
        )
        return messaging.send(message)


_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(channel: str, provider: BaseProvider) -> None:
    _REGISTRY[channel] = provider


def get_provider(channel: str) -> BaseProvider:
    if channel not in _REGISTRY:
        _REGISTRY[channel] = LogProvider(channel)
    return _REGISTRY[channel]


def configure_providers() -> None:
    """Регистрация боевых провайдеров по настройкам (вызывается из AppConfig.ready).

    Без ключей остаётся LogProvider — поведение dev/test не меняется."""
    from django.conf import settings

    credentials_file = getattr(settings, 'FIREBASE_CREDENTIALS_FILE', '')
    if credentials_file:
        try:
            register_provider('push', FCMProvider(credentials_file))
            logger.info('FCM push-провайдер зарегистрирован.')
        except Exception:  # noqa: BLE001 — недоступный Firebase не должен ронять приложение
            logger.exception('Не удалось инициализировать FCM-провайдер, используется LogProvider.')
