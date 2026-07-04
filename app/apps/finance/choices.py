from django.db import models


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Ожидает'
    PAID = 'paid', 'Оплачен'
    FAILED = 'failed', 'Ошибка'
    CANCELLED = 'cancelled', 'Отменён'
    REFUNDED = 'refunded', 'Возвращён'


class PaymentMethod(models.TextChoices):
    """Методы оплаты (ТЗ, раздел 11)."""

    CASH = 'cash', 'Наличные'
    CARD = 'card', 'Карта'
    BANK_TRANSFER = 'bank_transfer', 'Банковский перевод'
    QR = 'qr', 'QR-оплата'
    POS = 'pos', 'POS-терминал'
    ONLINE = 'online', 'Онлайн'


class InvoiceStatus(models.TextChoices):
    DRAFT = 'draft', 'Черновик'
    ISSUED = 'issued', 'Выставлен'
    PAID = 'paid', 'Оплачен'
    CANCELLED = 'cancelled', 'Отменён'


class TransactionType(models.TextChoices):
    INCOME = 'income', 'Доход'
    EXPENSE = 'expense', 'Расход'
    REFUND = 'refund', 'Возврат'
    TRANSFER = 'transfer', 'Перемещение'
    CORRECTION = 'correction', 'Корректировка'


class RefundReason(models.TextChoices):
    CUSTOMER_REQUEST = 'customer_request', 'Запрос клиента'
    CANCELLED_ORDER = 'cancelled_order', 'Отмена заказа'
    WRONG_PAYMENT = 'wrong_payment', 'Ошибочный платёж'
    DUPLICATE_PAYMENT = 'duplicate_payment', 'Дубль платежа'
    OTHER = 'other', 'Другое'


class DebtStatus(models.TextChoices):
    OPEN = 'open', 'Открыт'
    PARTIALLY_PAID = 'partially_paid', 'Частично погашен'
    CLOSED = 'closed', 'Закрыт'
    OVERDUE = 'overdue', 'Просрочен'
