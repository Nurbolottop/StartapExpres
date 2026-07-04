from apps.common import errors
from apps.common.exceptions import ConflictException, NotFoundException


class QRAlreadyGeneratedException(ConflictException):
    default_code = errors.PackageErrors.QR_ALREADY_EXISTS
    default_message = 'QR-код уже сгенерирован и не может быть изменён.'


class PackageNotFoundByQRException(NotFoundException):
    default_code = errors.PackageErrors.NOT_FOUND
    default_message = 'Груз с таким QR-кодом не найден.'


class PackageLockedException(ConflictException):
    default_code = errors.OrderErrors.LOCKED
    default_message = 'Состав заказа нельзя менять после отправки.'
