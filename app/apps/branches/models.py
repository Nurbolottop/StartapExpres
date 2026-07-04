from django.core.validators import RegexValidator
from django.db import models

from apps.common.models import BaseModel
from apps.common.validators import phone_validator

branch_code_validator = RegexValidator(
    regex=r'^[A-Z0-9]{2,10}$',
    message='Код филиала: 2–10 символов, только заглавные латинские буквы и цифры.',
)


class Branch(BaseModel):
    """Филиал компании. Точка приёма, хранения и выдачи грузов."""

    name = models.CharField('Название', max_length=150)
    code = models.CharField(
        'Код',
        max_length=10,
        unique=True,
        validators=[branch_code_validator],
        help_text='Короткий код филиала, используется в трек-номерах (например BSH).',
    )
    city = models.CharField('Город', max_length=100)
    address = models.CharField('Адрес', max_length=255, blank=True)
    phone = models.CharField('Телефон', max_length=16, blank=True, validators=[phone_validator])
    is_active = models.BooleanField('Действующий', default=True)

    class Meta:
        verbose_name = 'Филиал'
        verbose_name_plural = 'Филиалы'
        ordering = ('name',)

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'
