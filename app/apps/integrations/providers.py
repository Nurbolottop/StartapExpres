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


_REGISTRY: dict[str, BaseProvider] = {}


def register_provider(channel: str, provider: BaseProvider) -> None:
    _REGISTRY[channel] = provider


def get_provider(channel: str) -> BaseProvider:
    if channel not in _REGISTRY:
        _REGISTRY[channel] = LogProvider(channel)
    return _REGISTRY[channel]
