from apps.common import errors
from apps.common.exceptions import (
    AuthenticationException,
    BusinessException,
    ConflictException,
    ThrottledException,
)


class InvalidCredentialsException(AuthenticationException):
    default_code = errors.AuthErrors.INVALID_PASSWORD
    default_message = 'Неверный телефон или пароль.'


class UserBlockedException(AuthenticationException):
    status_code = 403
    default_code = errors.AuthErrors.USER_BLOCKED
    default_message = 'Пользователь заблокирован.'


class TooManyAttemptsException(ThrottledException):
    default_code = errors.AuthErrors.TOO_MANY_ATTEMPTS
    default_message = 'Слишком много попыток входа. Повторите через 30 минут.'


class InvalidRefreshTokenException(AuthenticationException):
    default_code = errors.AuthErrors.INVALID_REFRESH_TOKEN
    default_message = 'Недействительный refresh-токен.'


class SessionNotFoundException(AuthenticationException):
    status_code = 404
    default_code = errors.AuthErrors.INVALID_REFRESH_TOKEN
    default_message = 'Сессия не найдена.'


class LastSuperAdminException(ConflictException):
    default_code = errors.UserErrors.ROLE_FORBIDDEN
    default_message = 'Нельзя удалить или заблокировать последнего суперадминистратора.'


class SelfBlockException(ConflictException):
    default_code = errors.UserErrors.PERMISSION_DENIED
    default_message = 'Нельзя заблокировать или удалить самого себя.'


class RoleNotAllowedException(BusinessException):
    default_code = errors.UserErrors.ROLE_FORBIDDEN
    default_message = 'Назначение этой роли недоступно.'
