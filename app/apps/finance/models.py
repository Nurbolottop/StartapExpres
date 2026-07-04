from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.finance.choices import (
    DebtStatus,
    InvoiceStatus,
    PaymentMethod,
    PaymentStatus,
    RefundReason,
    TransactionType,
)

KGS = 'KGS'


class Payment(BaseModel):
    """Платёж (ТЗ, раздел 11). Удаление и изменение суммы запрещены."""

    payment_number = models.CharField('Номер', max_length=20, unique=True, editable=False)
    order = models.ForeignKey(
        'orders.Order', verbose_name='Заказ', related_name='payments', on_delete=models.PROTECT
    )
    amount = models.DecimalField(
        'Сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    currency = models.CharField('Валюта', max_length=3, default=KGS)
    payment_method = models.CharField('Метод', max_length=20, choices=PaymentMethod.choices)
    transaction_id = models.CharField('Внешний ID транзакции', max_length=100, blank=True)
    paid_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Плательщик',
        related_name='payments_made',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    paid_at = models.DateTimeField('Оплачен', null=True, blank=True)
    status = models.CharField(
        'Статус', max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.payment_number} ({self.amount} {self.currency})'


class Invoice(BaseModel):
    """Счёт (ТЗ, раздел 11). После оплаты не изменяется."""

    invoice_number = models.CharField('Номер', max_length=20, unique=True, editable=False)
    order = models.ForeignKey(
        'orders.Order', verbose_name='Заказ', related_name='invoices', on_delete=models.PROTECT
    )
    payment = models.ForeignKey(
        Payment,
        verbose_name='Платёж',
        related_name='invoices',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2)
    vat_percent = models.DecimalField('НДС, %', max_digits=5, decimal_places=2, default=12)
    issued_at = models.DateTimeField('Выставлен', null=True, blank=True)
    due_date = models.DateField('Срок оплаты', null=True, blank=True)
    status = models.CharField(
        'Статус', max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT
    )

    class Meta:
        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['status'])]

    def __str__(self) -> str:
        return f'{self.invoice_number} ({self.get_status_display()})'


class Cashbox(BaseModel):
    """Касса филиала — одна на филиал (ТЗ, раздел 11)."""

    branch = models.OneToOneField(
        'branches.Branch', verbose_name='Филиал', related_name='cashbox', on_delete=models.PROTECT
    )
    balance = models.DecimalField('Баланс', max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Касса'
        verbose_name_plural = 'Кассы'
        ordering = ('branch__name',)

    def __str__(self) -> str:
        return f'Касса {self.branch.name} ({self.balance})'


class CashSession(BaseModel):
    """Смена кассира (ТЗ, раздел 11)."""

    cashbox = models.ForeignKey(
        Cashbox, verbose_name='Касса', related_name='sessions', on_delete=models.PROTECT
    )
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Кассир',
        related_name='cash_sessions',
        on_delete=models.PROTECT,
    )
    opened_at = models.DateTimeField('Открыта', auto_now_add=True)
    closed_at = models.DateTimeField('Закрыта', null=True, blank=True)
    opening_balance = models.DecimalField('Остаток на открытие', max_digits=14, decimal_places=2)
    closing_balance = models.DecimalField(
        'Остаток на закрытие', max_digits=14, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = 'Кассовая смена'
        verbose_name_plural = 'Кассовые смены'
        ordering = ('-opened_at',)
        constraints = [
            models.UniqueConstraint(
                fields=['cashbox'],
                condition=models.Q(closed_at__isnull=True),
                name='single_open_session_per_cashbox',
            ),
        ]

    def __str__(self) -> str:
        state = 'открыта' if self.closed_at is None else 'закрыта'
        return f'Смена {self.cashbox_id} ({state})'


class Transaction(BaseModel):
    """Движение денег (ТЗ, раздел 11). Любая операция — отдельная запись."""

    cashbox = models.ForeignKey(
        Cashbox, verbose_name='Касса', related_name='transactions', on_delete=models.PROTECT
    )
    payment = models.ForeignKey(
        Payment,
        verbose_name='Платёж',
        related_name='transactions',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    amount = models.DecimalField('Сумма', max_digits=12, decimal_places=2)
    type = models.CharField('Тип', max_length=20, choices=TransactionType.choices)
    comment = models.CharField('Комментарий', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['cashbox', 'type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self) -> str:
        return f'{self.get_type_display()} {self.amount}'


class Refund(BaseModel):
    """Возврат платежа (ТЗ, раздел 11)."""

    payment = models.ForeignKey(
        Payment, verbose_name='Платёж', related_name='refunds', on_delete=models.PROTECT
    )
    amount = models.DecimalField(
        'Сумма', max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)]
    )
    reason = models.CharField('Причина', max_length=30, choices=RefundReason.choices)
    comment = models.CharField('Комментарий', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Возврат'
        verbose_name_plural = 'Возвраты'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Возврат {self.amount} по {self.payment_id}'


class Debt(BaseModel):
    """Задолженность по постоплате (ТЗ, раздел 11)."""

    order = models.OneToOneField(
        'orders.Order', verbose_name='Заказ', related_name='debt', on_delete=models.PROTECT
    )
    amount = models.DecimalField('Сумма долга', max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField('Погашено', max_digits=12, decimal_places=2, default=0)
    due_date = models.DateField('Срок оплаты')
    status = models.CharField('Статус', max_length=20, choices=DebtStatus.choices, default=DebtStatus.OPEN)

    class Meta:
        verbose_name = 'Задолженность'
        verbose_name_plural = 'Задолженности'
        ordering = ('due_date',)
        indexes = [models.Index(fields=['status', 'due_date'])]

    def __str__(self) -> str:
        return f'Долг {self.amount} по {self.order_id}'


class FinancialReport(BaseModel):
    """Финансовый отчёт за период (ТЗ, раздел 11). Формируется автоматически."""

    period_type = models.CharField('Период', max_length=10)  # daily / monthly / yearly
    period_date = models.DateField('Дата периода')
    data = models.JSONField('Показатели', default=dict)

    class Meta:
        verbose_name = 'Финансовый отчёт'
        verbose_name_plural = 'Финансовые отчёты'
        ordering = ('-period_date',)
        constraints = [
            models.UniqueConstraint(fields=['period_type', 'period_date'], name='unique_report_per_period'),
        ]

    def __str__(self) -> str:
        return f'{self.period_type} {self.period_date}'
