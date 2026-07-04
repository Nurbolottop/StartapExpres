"""Общие сервисы: генерация человекочитаемых номеров (ТЗ, разделы 07, 26).

Формат: ORD-2026-000001. Счётчик атомарный (select_for_update),
безопасен при конкурентной генерации.
"""

from django.db import transaction
from django.utils import timezone

from apps.common.models import NumberSequence


def generate_number(prefix: str, *, yearly: bool = True, width: int = 6) -> str:
    """Выдаёт следующий номер последовательности: CLT-000001, ORD-2026-000001."""
    year = timezone.now().year
    scope = f'{prefix}-{year}' if yearly else prefix
    with transaction.atomic():
        sequence, _ = NumberSequence.objects.select_for_update().get_or_create(scope=scope)
        sequence.last_value += 1
        sequence.save(update_fields=['last_value'])
    number = str(sequence.last_value).zfill(width)
    return f'{prefix}-{year}-{number}' if yearly else f'{prefix}-{number}'
