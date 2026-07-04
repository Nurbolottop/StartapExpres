"""Шифрование персональных данных на уровне полей (ТЗ, раздел 30)."""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models

_PREFIX = 'enc:'


def _fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class EncryptedCharField(models.CharField):
    """Хранит значение зашифрованным (AES-128-CBC + HMAC, Fernet).

    Прозрачно шифрует при записи и расшифровывает при чтении.
    Поиск/фильтрация по такому полю невозможны — только точное чтение.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 512)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        if not value or str(value).startswith(_PREFIX):
            return value
        token = _fernet().encrypt(str(value).encode()).decode()
        return f'{_PREFIX}{token}'

    def from_db_value(self, value, expression, connection):
        if not value or not value.startswith(_PREFIX):
            return value
        try:
            return _fernet().decrypt(value[len(_PREFIX) :].encode()).decode()
        except InvalidToken:
            return value
