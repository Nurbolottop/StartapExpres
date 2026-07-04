from apps.common import errors
from apps.common.exceptions import BusinessException, ConflictException


class PaymentAlreadyRefundedException(ConflictException):
    default_code = errors.PaymentErrors.REFUND_FAILED
    default_message = 'Платёж уже возвращён.'


class RefundExceedsPaymentException(BusinessException):
    default_code = errors.PaymentErrors.REFUND_FAILED
    default_message = 'Сумма возврата превышает сумму платежа.'


class CashboxSessionException(ConflictException):
    default_code = errors.PaymentErrors.FAILED
    default_message = 'Кассовая смена уже открыта или не найдена.'


class DebtClosedException(ConflictException):
    default_code = errors.PaymentErrors.DEBT_EXISTS
    default_message = 'Задолженность уже закрыта.'


class OrderFinanceIncompleteException(BusinessException):
    default_code = errors.PaymentErrors.DEBT_EXISTS
    default_message = 'Заказ нельзя завершить: оплата не закрыта (ТЗ, раздел 11).'
