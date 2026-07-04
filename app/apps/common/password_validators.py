"""Парольная политика (ТЗ, раздел 30): минимум 12 символов, буквы в обоих
регистрах, цифра и спецсимвол."""

import re

from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    _rules = (
        (r'[A-ZА-Я]', 'заглавную букву'),
        (r'[a-zа-я]', 'строчную букву'),
        (r'\d', 'цифру'),
        (r'[^\w\s]|_', 'специальный символ'),
    )

    def validate(self, password: str, user=None) -> None:
        missing = [name for pattern, name in self._rules if not re.search(pattern, password)]
        if missing:
            raise ValidationError(
                f'Пароль должен содержать: {", ".join(missing)}.',
                code='password_too_simple',
            )

    def get_help_text(self) -> str:
        return 'Пароль должен содержать заглавную и строчную буквы, цифру и специальный символ.'
