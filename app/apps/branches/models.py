from django.core.validators import RegexValidator
from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import phone_validator

code_validator = RegexValidator(
    regex=r'^[A-Z0-9]{2,10}$',
    message='Код: 2–10 символов, только заглавные латинские буквы и цифры.',
)


class City(BaseModel):
    """Город (ТЗ, раздел 02: BRANCHES)."""

    name = models.CharField('Название', max_length=100)
    code = models.CharField('Код', max_length=10, unique=True, validators=[code_validator])
    country = models.CharField('Страна', max_length=100, default='Кыргызстан')
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ('name',)
        indexes = [models.Index(fields=['name'])]

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'


class Branch(BaseModel):
    """Филиал компании (ТЗ, раздел 02: BRANCHES)."""

    city = models.ForeignKey(City, verbose_name='Город', related_name='branches', on_delete=models.PROTECT)
    name = models.CharField('Название', max_length=150)
    code = models.CharField(
        'Код',
        max_length=10,
        unique=True,
        validators=[code_validator],
        help_text='Короткий код филиала, используется в номерах и маркировке.',
    )
    address = models.CharField('Адрес', max_length=255, blank=True)
    phone = models.CharField('Телефон', max_length=16, blank=True, validators=[phone_validator])
    email = models.EmailField('Email', blank=True)
    is_main = models.BooleanField('Главный филиал', default=False)
    opening_time = models.TimeField('Открытие', null=True, blank=True)
    closing_time = models.TimeField('Закрытие', null=True, blank=True)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ('name',)
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'
