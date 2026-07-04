from apps.common import errors
from apps.common.exceptions import BusinessException, ConflictException


class CellFullException(BusinessException):
    default_code = errors.WarehouseErrors.CELL_FULL
    default_message = 'Ячейка переполнена: превышен вес или объём.'


class CellNotEmptyException(ConflictException):
    default_code = errors.WarehouseErrors.INVALID_MOVEMENT
    default_message = 'Нельзя удалить ячейку, в которой находится груз.'


class ZoneNotEmptyException(ConflictException):
    default_code = errors.WarehouseErrors.INVALID_MOVEMENT
    default_message = 'Нельзя удалить зону, в которой есть ячейки.'


class WarehouseNotEmptyException(ConflictException):
    default_code = errors.WarehouseErrors.INVALID_MOVEMENT
    default_message = 'Нельзя удалить склад, в котором есть зоны или грузы.'
