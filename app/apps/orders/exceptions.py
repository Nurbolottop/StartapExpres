from apps.common import errors
from apps.common.exceptions import BusinessException, ConflictException, PermissionException


class InvalidStatusTransitionException(ConflictException):
    default_code = errors.OrderErrors.INVALID_STATUS
    default_message = 'Недопустимый переход статуса заказа.'


class TransitionRoleException(PermissionException):
    default_code = errors.OrderErrors.INVALID_STATUS
    default_message = 'Роль не позволяет выполнить этот переход статуса.'


class OrderLockedException(ConflictException):
    default_code = errors.OrderErrors.LOCKED
    default_message = 'Заказ отправлен и больше не может быть изменён.'


class FrozenFieldsException(ConflictException):
    default_code = errors.OrderErrors.LOCKED
    default_message = 'После подтверждения нельзя менять стороны, филиалы и стоимость.'


class OrderVersionConflictException(ConflictException):
    default_code = errors.CONFLICT
    default_message = 'Заказ был изменён другим пользователем. Обновите данные.'


class OrderAlreadyPaidException(ConflictException):
    default_code = errors.OrderErrors.ALREADY_PAID
    default_message = 'Заказ уже оплачен.'


class PackagesRequiredException(BusinessException):
    default_code = errors.OrderErrors.PACKAGE_MISSING
    default_message = 'Заказ должен содержать хотя бы одно грузовое место.'


class ClientCancelForbiddenException(PermissionException):
    default_code = errors.OrderErrors.LOCKED
    default_message = 'Клиент может отменить заказ только до подтверждения.'
