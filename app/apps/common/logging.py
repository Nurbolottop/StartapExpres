import logging
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar('request_id', default='-')


class RequestIDFilter(logging.Filter):
    """Добавляет request_id текущего запроса в каждую запись лога."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True
