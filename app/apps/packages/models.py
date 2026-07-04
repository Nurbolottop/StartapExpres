import uuid
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel
from apps.packages.choices import PackageStatus, PhotoType


def package_photo_path(instance, filename: str) -> str:
    return f'packages/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class Package(BaseModel):
    """Грузовое место заказа (ТЗ, раздел 02: PACKAGE).

    QR генерируется один раз и никогда не меняется (ТЗ, разделы 06, 08).
    """

    order = models.ForeignKey(
        'orders.Order', verbose_name='Заказ', related_name='packages', on_delete=models.PROTECT
    )
    qr_code = models.CharField('QR-код', max_length=64, unique=True, null=True, blank=True)
    barcode = models.CharField('Штрихкод', max_length=64, unique=True, null=True, blank=True)
    qr_generated_at = models.DateTimeField('QR создан', null=True, blank=True, editable=False)
    title = models.CharField('Наименование', max_length=255)
    description = models.TextField('Описание', blank=True)
    weight = models.DecimalField(
        'Вес, кг', max_digits=10, decimal_places=3, validators=[MinValueValidator(Decimal('0.001'))]
    )
    length = models.PositiveIntegerField('Длина, см', null=True, blank=True)
    width = models.PositiveIntegerField('Ширина, см', null=True, blank=True)
    height = models.PositiveIntegerField('Высота, см', null=True, blank=True)
    volume = models.DecimalField(
        'Объём, м³', max_digits=10, decimal_places=3, default=0, validators=[MinValueValidator(0)]
    )
    declared_price = models.DecimalField(
        'Объявленная ценность',
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    fragile = models.BooleanField('Хрупкий', default=False)
    dangerous = models.BooleanField('Опасный', default=False)
    status = models.CharField(
        'Статус', max_length=20, choices=PackageStatus.choices, default=PackageStatus.CREATED
    )

    class Meta:
        verbose_name = 'Грузовое место'
        verbose_name_plural = 'Грузовые места'
        ordering = ('created_at',)
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order', 'status']),
        ]

    def __str__(self) -> str:
        return f'{self.title} ({self.order.order_number})'

    def save(self, *args, **kwargs):
        self.qr_code = self.qr_code or None
        self.barcode = self.barcode or None
        if self.length and self.width and self.height and not self.volume:
            self.volume = round(self.length * self.width * self.height / 1_000_000, 3)
        super().save(*args, **kwargs)


class PackagePhoto(BaseModel):
    """Фотофиксация груза (ТЗ, раздел 02: PackagePhoto)."""

    package = models.ForeignKey(Package, verbose_name='Груз', related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField('Фото', upload_to=package_photo_path)
    type = models.CharField('Этап', max_length=20, choices=PhotoType.choices)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Загрузил',
        related_name='package_photos',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = 'Фото груза'
        verbose_name_plural = 'Фото грузов'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['package', 'type'])]

    def __str__(self) -> str:
        return f'{self.package_id}: {self.get_type_display()}'
