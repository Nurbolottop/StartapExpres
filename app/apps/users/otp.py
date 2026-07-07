"""Одноразовые SMS-коды (OTP): восстановление пароля, верификация телефона.

Коды живут в Redis-кэше (TTL 10 минут), повторный запрос — не чаще раза
в минуту, максимум 5 попыток ввода на один код (ТЗ, раздел 30).
"""

import secrets

from django.core.cache import cache
from django.utils.translation import gettext as _

from apps.users import exceptions

OTP_TTL_SECONDS = 10 * 60
OTP_RESEND_COOLDOWN_SECONDS = 60
OTP_MAX_ATTEMPTS = 5

PURPOSE_PASSWORD_RESET = 'password_reset'
PURPOSE_PHONE_VERIFY = 'phone_verify'


def _code_key(purpose: str, phone: str) -> str:
    return f'otp:{purpose}:code:{phone}'


def _attempts_key(purpose: str, phone: str) -> str:
    return f'otp:{purpose}:attempts:{phone}'


def _cooldown_key(purpose: str, phone: str) -> str:
    return f'otp:{purpose}:cooldown:{phone}'


class OTPService:
    @staticmethod
    def issue(*, phone: str, purpose: str) -> str:
        """Генерирует код и ставит cooldown на повторный запрос."""
        if cache.get(_cooldown_key(purpose, phone)):
            raise exceptions.OTPCooldownException()
        code = f'{secrets.randbelow(1_000_000):06d}'
        cache.set(_code_key(purpose, phone), code, timeout=OTP_TTL_SECONDS)
        cache.set(_attempts_key(purpose, phone), 0, timeout=OTP_TTL_SECONDS)
        cache.set(_cooldown_key(purpose, phone), True, timeout=OTP_RESEND_COOLDOWN_SECONDS)
        return code

    @staticmethod
    def verify(*, phone: str, purpose: str, code: str) -> None:
        """Проверяет код; сжигает его при успехе, считает неудачные попытки."""
        stored = cache.get(_code_key(purpose, phone))
        if stored is None:
            raise exceptions.OTPInvalidException()

        attempts_key = _attempts_key(purpose, phone)
        if not cache.add(attempts_key, 1, timeout=OTP_TTL_SECONDS):
            attempts = cache.incr(attempts_key)
        else:
            attempts = 1
        if attempts > OTP_MAX_ATTEMPTS:
            cache.delete_many([_code_key(purpose, phone), attempts_key])
            raise exceptions.OTPInvalidException(_('Превышено число попыток. Запросите новый код.'))

        if not secrets.compare_digest(str(stored), str(code)):
            raise exceptions.OTPInvalidException()

        cache.delete_many([_code_key(purpose, phone), attempts_key])
