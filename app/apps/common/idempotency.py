"""Идемпотентность критических POST-запросов (ТЗ, разделы 22, 25).

Клиент передаёт заголовок Idempotency-Key; повторный запрос с тем же ключом
возвращает сохранённый ответ и не выполняет операцию повторно.
"""

import functools

from django.core.cache import cache
from rest_framework.response import Response

IDEMPOTENCY_TTL = 24 * 60 * 60  # 24 часа


def idempotent(view_method):
    """Декоратор для методов APIView/ViewSet, обрабатывающих критические POST."""

    @functools.wraps(view_method)
    def wrapper(self, request, *args, **kwargs):
        key = request.headers.get('Idempotency-Key')
        if not key:
            return view_method(self, request, *args, **kwargs)

        user_id = request.user.id if request.user.is_authenticated else 'anon'
        cache_key = f'idem:{user_id}:{request.path}:{key}'
        saved = cache.get(cache_key)
        if saved is not None:
            return Response(saved['data'], status=saved['status'])

        response = view_method(self, request, *args, **kwargs)
        if 200 <= response.status_code < 300:
            cache.set(
                cache_key, {'data': response.data, 'status': response.status_code}, timeout=IDEMPOTENCY_TTL
            )
        return response

    return wrapper
