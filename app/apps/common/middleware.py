import time
import uuid

from apps.common.logging import request_context


class RequestContextMiddleware:
    """Сквозные Request-ID / Correlation-ID, время выполнения и версия API
    (ТЗ, разделы 24–25).

    Контекст запроса (ip, user agent, идентификаторы) складывается в
    contextvar и доступен логам и подписчикам событий (audit).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.monotonic()
        request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        correlation_id = request.headers.get('X-Correlation-ID') or request_id

        request.request_id = request_id
        request.correlation_id = correlation_id
        request_context.set(
            {
                'request_id': request_id,
                'correlation_id': correlation_id,
                'ip': self._client_ip(request),
                'user_agent': request.headers.get('User-Agent', '')[:512],
            }
        )

        response = self.get_response(request)

        execution_ms = int((time.monotonic() - started_at) * 1000)
        response['X-Request-ID'] = request_id
        response['X-Correlation-ID'] = correlation_id
        response['X-API-Version'] = 'v1'
        response['X-Execution-Time'] = f'{execution_ms} ms'
        return response

    @staticmethod
    def _client_ip(request) -> str:
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
