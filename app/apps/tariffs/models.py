from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class Tariff(BaseModel):
    """Тариф направления (ТЗ, разделы 04, 07: расчёт стоимости).

    from_city/to_city = NULL — тариф по умолчанию для любых направлений.
    """

    name = models.CharField('Название', max_length=150)
    code = models.CharField('Код', max_length=20, unique=True)
    from_city = models.ForeignKey(
        'branches.City',
        verbose_name='Откуда',
        related_name='tariffs_from',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    to_city = models.ForeignKey(
        'branches.City',
        verbose_name='Куда',
        related_name='tariffs_to',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    base_price = models.DecimalField(
        'Базовая цена', max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    price_per_kg = models.DecimalField(
        'Цена за кг', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    price_per_m3 = models.DecimalField(
        'Цена за м³', max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    min_price = models.DecimalField(
        'Минимальная стоимость',
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    insurance_percent = models.DecimalField(
        'Страховка, % от объявленной ценности',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )

    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['from_city', 'to_city'],
                condition=models.Q(is_deleted=False),
                name='unique_active_tariff_per_route',
            ),
        ]
        indexes = [models.Index(fields=['from_city', 'to_city'])]

    def __str__(self) -> str:
        route = f'{self.from_city or "*"} → {self.to_city or "*"}'
        return f'{self.name} ({route})'


class AdditionalService(BaseModel):
    """Дополнительная услуга заказа (ТЗ, раздел 07): упаковка, доставка до
    двери, экспресс, хрупкий груз, подъём на этаж и т.д."""

    name = models.CharField('Название', max_length=150)
    code = models.CharField('Код', max_length=30, unique=True)
    price = models.DecimalField('Цена', max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Дополнительная услуга'
        verbose_name_plural = 'Дополнительные услуги'
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} ({self.price})'
