from apps.common import errors
from apps.common.exceptions import BusinessException


class VehicleUnavailableException(BusinessException):
    default_code = errors.ShipmentErrors.VEHICLE_BUSY
    default_message = 'Автомобиль занят или не готов к назначению.'


class DriverUnavailableException(BusinessException):
    default_code = errors.ShipmentErrors.DRIVER_BUSY
    default_message = 'Водитель занят или не может быть назначен.'
