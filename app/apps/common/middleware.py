import uuid

from apps.common.logging import request_id_var


class RequestIDMiddleware:
    """Сквозной идентификатор запроса: принимает X-Request-ID от клиента/прокси
    или генерирует свой; пробрасывает его в логи и заголовок ответа."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        request_id_var.set(request_id)
        request.request_id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response
