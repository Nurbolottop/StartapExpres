from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.accounts.constants import Roles
from apps.accounts.managers import UserManager
from apps.common.models import TimeStampedModel, UUIDModel
from apps.common.validators import phone_validator


class User(UUIDModel, TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    """Единая модель пользователя системы: сотрудники и клиенты.

    Аутентификация по номеру телефона. Права определяются полем role.
    """

    phone = models.CharField(
        'Телефон',
        max_length=16,
        unique=True,
        validators=[phone_validator],
        error_messages={'unique': 'Пользователь с таким телефоном уже существует.'},
    )
    email = models.EmailField('Email', blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    first_name = models.CharField('Имя', max_length=150, blank=True)
    middle_name = models.CharField('Отчество', max_length=150, blank=True)

    role = models.CharField(
        'Роль',
        max_length=20,
        choices=Roles.choices,
        default=Roles.CLIENT,
        db_index=True,
    )
    branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал',
        related_name='users',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text='Филиал, к которому привязан сотрудник. Для клиентов не заполняется.',
    )

    is_active = models.BooleanField('Активен', default=True)
    is_staff = models.BooleanField('Доступ в админку', default=False)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'{self.full_name} ({self.phone})' if self.full_name else self.phone

    @property
    def full_name(self) -> str:
        return ' '.join(part for part in (self.last_name, self.first_name, self.middle_name) if part)
