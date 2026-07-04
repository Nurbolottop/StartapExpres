"""Единый формат ошибок API.

Все ошибки возвращаются в виде:
    {"error": {"code": "<machine_code>", "message": "<человекочитаемое>", "details": {...}}}

Сервисный слой бросает ApplicationError (и наследников) — HTTP-статус
определяется классом исключения, а не местом вызова.
"""
import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class ApplicationError(Exception):
    """Базовое доменное исключение сервисного слоя."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'application_error'
    default_message = 'Ошибка выполнения операции.'

    def __init__(self, message: str | None = None, *, code: str | None = None, details: dict | None = None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = 'not_found'
    default_message = 'Объект не найден.'


class ConflictError(ApplicationError):
    status_code = status.HTTP_409_CONFLICT
    default_code = 'conflict'
    default_message = 'Конфликт данных.'


class PermissionDeniedError(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = 'permission_denied'
    default_message = 'Недостаточно прав для выполнения операции.'


def _error_payload(code: str, message: str, details) -> dict:
    return {'error': {'code': code, 'message': message, 'details': details}}


def exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        exc = exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, ProtectedError):
        exc = ConflictError(
            'Объект используется другими записями и не может быть удалён.',
            code='protected_object',
        )

    if isinstance(exc, ApplicationError):
        logger.info('ApplicationError: %s (code=%s)', exc.message, exc.code)
        return Response(
            _error_payload(exc.code, exc.message, exc.details),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        # Необработанное исключение — стандартный 500 Django + лог
        logger.exception('Необработанное исключение в %s', context.get('view'))
        return None

    if isinstance(exc, exceptions.ValidationError):
        code = 'validation_error'
        message = 'Ошибка валидации данных.'
        details = response.data
    else:
        code = getattr(exc, 'default_code', 'error')
        detail = getattr(exc, 'detail', None)
        message = str(detail) if isinstance(detail, (str, exceptions.ErrorDetail)) else str(
            getattr(exc, 'default_detail', 'Ошибка запроса.')
        )
        details = {}

    response.data = _error_payload(code, message, details)
    return response
