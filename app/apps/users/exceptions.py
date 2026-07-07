from django.utils.translation import gettext_lazy as _

from apps.common import errors
from apps.common.exceptions import (
    AuthenticationException,
    BusinessException,
    ConflictException,
    ThrottledException,
    ValidationException,
)


class OTPInvalidException(ValidationException):
    default_code = errors.AuthErrors.OTP_INVALID
    default_message = _('Неверный или истёкший код подтверждения.')


class OTPCooldownException(ThrottledException):
    default_code = errors.AuthErrors.OTP_COOLDOWN
    default_message = _('Код уже отправлен. Повторный запрос — через минуту.')


class InvalidCredentialsException(AuthenticationException):
    default_code = errors.AuthErrors.INVALID_PASSWORD
    default_message = _('Неверный телефон или пароль.')


class UserBlockedException(AuthenticationException):
    status_code = 403
    default_code = errors.AuthErrors.USER_BLOCKED
    default_message = _('Пользователь заблокирован.')


class TooManyAttemptsException(ThrottledException):
    default_code = errors.AuthErrors.TOO_MANY_ATTEMPTS
    default_message = _('Слишком много попыток входа. Повторите через 30 минут.')


class InvalidRefreshTokenException(AuthenticationException):
    default_code = errors.AuthErrors.INVALID_REFRESH_TOKEN
    default_message = _('Недействительный refresh-токен.')


class SessionNotFoundException(AuthenticationException):
    status_code = 404
    default_code = errors.AuthErrors.INVALID_REFRESH_TOKEN
    default_message = _('Сессия не найдена.')


class LastSuperAdminException(ConflictException):
    default_code = errors.UserErrors.ROLE_FORBIDDEN
    default_message = _('Нельзя удалить или заблокировать последнего суперадминистратора.')


class SelfBlockException(ConflictException):
    default_code = errors.UserErrors.PERMISSION_DENIED
    default_message = _('Нельзя заблокировать или удалить самого себя.')


class RoleNotAllowedException(BusinessException):
    default_code = errors.UserErrors.ROLE_FORBIDDEN
    default_message = _('Назначение этой роли недоступно.')
