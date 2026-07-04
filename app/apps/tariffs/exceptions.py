from apps.common import errors
from apps.common.exceptions import BusinessException


class TariffNotFoundException(BusinessException):
    default_code = errors.TariffErrors.NOT_FOUND
    default_message = 'Тариф для указанного направления не найден.'
