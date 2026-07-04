import logging
from contextvars import ContextVar

request_context: ContextVar[dict] = ContextVar('request_context', default={})


class RequestContextFilter(logging.Filter):
    """Добавляет request_id/correlation_id текущего запроса в записи лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        context = request_context.get()
        record.request_id = context.get('request_id', '-')
        record.correlation_id = context.get('correlation_id', '-')
        return True
