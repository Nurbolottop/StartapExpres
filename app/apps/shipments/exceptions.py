from apps.common import errors
from apps.common.exceptions import BusinessException, ConflictException, PermissionException


class InvalidShipmentTransitionException(ConflictException):
    default_code = errors.ShipmentErrors.STARTED
    default_message = 'Недопустимый переход статуса рейса.'


class ShipmentTransitionRoleException(PermissionException):
    default_code = errors.ShipmentErrors.STARTED
    default_message = 'Роль не позволяет выполнить этот переход статуса рейса.'


class VehicleBusyException(BusinessException):
    default_code = errors.ShipmentErrors.VEHICLE_BUSY
    default_message = 'Автомобиль уже занят в другом активном рейсе.'


class DriverBusyException(BusinessException):
    default_code = errors.ShipmentErrors.DRIVER_BUSY
    default_message = 'Водитель уже занят в другом активном рейсе.'


class OrderNotReadyException(BusinessException):
    default_code = errors.OrderErrors.PAYMENT_REQUIRED
    default_message = 'В рейс можно добавить только оплаченный заказ, готовый к отправке.'


class OrderAlreadyInShipmentException(ConflictException):
    default_code = errors.OrderErrors.SHIPMENT_ASSIGNED
    default_message = 'Заказ уже находится в активном рейсе.'


class WeightLimitException(BusinessException):
    default_code = errors.ShipmentErrors.WEIGHT_LIMIT
    default_message = 'Превышена грузоподъёмность автомобиля.'


class VolumeLimitException(BusinessException):
    default_code = errors.ShipmentErrors.VOLUME_LIMIT
    default_message = 'Превышен допустимый объём автомобиля.'


class MissingPackageException(BusinessException):
    default_code = errors.ShipmentErrors.MISSING_PACKAGE
    default_message = 'Не все грузы рейса отсканированы.'


class ShipmentLockedException(ConflictException):
    default_code = errors.ShipmentErrors.STARTED
    default_message = 'Состав рейса нельзя менять после старта.'


class ShipmentChecklistException(BusinessException):
    default_code = errors.ShipmentErrors.INVALID_ROUTE
    default_message = 'Не выполнены условия отправки рейса.'
