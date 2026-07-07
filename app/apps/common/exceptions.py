"""Иерархия исключений и глобальный обработчик (ТЗ, разделы 24–25).

Формат ошибки:
    {"success": false, "message": "...", "error": {"code": "...", "details": {...}}}
Для ошибок валидации вместо details используется fields.
"""

import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models.deletion import ProtectedError
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

from apps.common import errors

logger = logging.getLogger(__name__)


class BaseAppException(Exception):
    """Базовое исключение системы. Все доменные исключения наследуются от него."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = errors.SystemErrors.UNKNOWN
    default_message = _lazy('Ошибка выполнения операции.')

    def __init__(self, message: str | None = None, *, code: str | None = None, details: dict | None = None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(BaseAppException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = errors.VALIDATION_ERROR
    default_message = _lazy('Ошибка валидации данных.')


class AuthenticationException(BaseAppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = errors.AuthErrors.INVALID_PASSWORD
    default_message = _lazy('Ошибка аутентификации.')


class PermissionException(BaseAppException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = errors.PERMISSION_DENIED
    default_message = _lazy('Недостаточно прав для выполнения операции.')


class NotFoundException(BaseAppException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = errors.NOT_FOUND
    default_message = _lazy('Объект не найден.')


class ConflictException(BaseAppException):
    status_code = status.HTTP_409_CONFLICT
    default_code = errors.CONFLICT
    default_message = _lazy('Конфликт данных.')


class BusinessException(BaseAppException):
    """Нарушение бизнес-правила (ТЗ, раздел 24: HTTP 422)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_code = errors.SystemErrors.UNKNOWN
    default_message = _lazy('Операция нарушает бизнес-правила.')


class ThrottledException(BaseAppException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_code = errors.AuthErrors.TOO_MANY_ATTEMPTS
    default_message = _lazy('Слишком много запросов. Повторите позже.')


class IntegrationException(BaseAppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_code = errors.SystemErrors.EXTERNAL_PROVIDER
    default_message = _lazy('Ошибка внешнего сервиса.')


def _error_body(message, code: str, *, details=None, fields=None) -> dict:
    error: dict = {'code': code}
    if fields is not None:
        error['fields'] = fields
    else:
        error['details'] = details or {}
    return {'success': False, 'message': str(message), 'error': error}


def exception_handler(exc, context):
    """Глобальный обработчик: любые исключения → единый конверт ошибки."""
    if isinstance(exc, DjangoValidationError):
        exc = drf_exceptions.ValidationError(as_serializer_error(exc))

    if isinstance(exc, ProtectedError):
        exc = ConflictException(_('Объект используется другими записями и не может быть удалён.'))

    if isinstance(exc, BaseAppException):
        logger.info('%s: %s (code=%s)', type(exc).__name__, exc.message, exc.code)
        return Response(
            _error_body(exc.message, exc.code, details=exc.details),
            status=exc.status_code,
        )

    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception('Необработанное исключение в %s', context.get('view'))
        return None

    if isinstance(exc, drf_exceptions.ValidationError):
        response.data = _error_body(
            _('Ошибка валидации данных.'), errors.VALIDATION_ERROR, fields=response.data
        )
        return response

    code_map = {
        drf_exceptions.NotAuthenticated: (_lazy('Unauthorized'), errors.AuthErrors.INVALID_PASSWORD),
        drf_exceptions.AuthenticationFailed: (_lazy('Unauthorized'), errors.AuthErrors.TOKEN_EXPIRED),
        drf_exceptions.PermissionDenied: (_lazy('Permission denied'), errors.PERMISSION_DENIED),
        drf_exceptions.NotFound: (_lazy('Object not found'), errors.NOT_FOUND),
        drf_exceptions.Throttled: (_lazy('Too many requests'), errors.AuthErrors.TOO_MANY_ATTEMPTS),
        drf_exceptions.MethodNotAllowed: (_lazy('Method not allowed'), errors.SystemErrors.UNKNOWN),
    }
    for exc_class, (message, code) in code_map.items():
        if isinstance(exc, exc_class):
            response.data = _error_body(message, code)
            return response

    detail = getattr(exc, 'detail', None)
    message = str(detail) if isinstance(detail, (str, drf_exceptions.ErrorDetail)) else _('Ошибка запроса.')
    response.data = _error_body(message, getattr(exc, 'default_code', errors.SystemErrors.UNKNOWN))
    return response
