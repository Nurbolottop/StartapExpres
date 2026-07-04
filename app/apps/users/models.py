import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.common.fields import EncryptedCharField
from apps.common.models import BaseModel
from apps.common.validators import phone_validator
from apps.users.choices import DriverStatus, EmployeeStatus, Languages, Roles
from apps.users.managers import UserManager


def avatar_upload_path(instance, filename: str) -> str:
    return f'avatars/{uuid.uuid4().hex}{Path(filename).suffix.lower()}'


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    """Единая модель пользователя (ТЗ, раздел 02). Аутентификация по телефону."""

    phone = models.CharField(
        'Телефон',
        max_length=16,
        unique=True,
        validators=[phone_validator],
        error_messages={'unique': 'Пользователь с таким телефоном уже существует.'},
    )
    email = models.EmailField(
        'Email',
        unique=True,
        null=True,
        blank=True,
        error_messages={'unique': 'Пользователь с таким email уже существует.'},
    )
    username = models.CharField('Логин', max_length=150, unique=True, null=True, blank=True)
    last_name = models.CharField('Фамилия', max_length=150, blank=True)
    first_name = models.CharField('Имя', max_length=150, blank=True)
    middle_name = models.CharField('Отчество', max_length=150, blank=True)

    role = models.CharField('Роль', max_length=20, choices=Roles.choices, default=Roles.CLIENT)
    avatar = models.ImageField('Аватар', upload_to=avatar_upload_path, null=True, blank=True)
    language = models.CharField('Язык', max_length=2, choices=Languages.choices, default=Languages.RUSSIAN)
    timezone = models.CharField('Часовой пояс', max_length=64, default='Asia/Bishkek')

    is_verified = models.BooleanField('Подтверждён', default=False)
    is_staff = models.BooleanField('Доступ в админку', default=False)

    objects = UserManager()
    all_objects = models.Manager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
            models.Index(fields=['role', 'is_active']),
        ]

    def __str__(self) -> str:
        return f'{self.full_name} ({self.phone})' if self.full_name else self.phone

    def save(self, *args, **kwargs):
        self.email = self.email or None
        self.username = self.username or None
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return ' '.join(part for part in (self.last_name, self.first_name, self.middle_name) if part)


class ClientProfile(BaseModel):
    """Профиль клиента (ТЗ, раздел 02)."""

    user = models.OneToOneField(
        User, verbose_name='Пользователь', related_name='client_profile', on_delete=models.CASCADE
    )
    client_code = models.CharField('Код клиента', max_length=20, unique=True)
    company_name = models.CharField('Компания', max_length=255, blank=True)
    passport_number = EncryptedCharField('Номер паспорта', blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    notes = models.TextField('Заметки', blank=True)
    discount_percent = models.DecimalField('Скидка, %', max_digits=5, decimal_places=2, default=0)
    balance = models.DecimalField('Баланс', max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Профиль клиента'
        verbose_name_plural = 'Профили клиентов'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['company_name'])]

    def __str__(self) -> str:
        return f'{self.client_code} — {self.user}'


class EmployeeProfile(BaseModel):
    """Профиль сотрудника (ТЗ, раздел 02)."""

    user = models.OneToOneField(
        User, verbose_name='Пользователь', related_name='employee_profile', on_delete=models.CASCADE
    )
    employee_code = models.CharField('Код сотрудника', max_length=20, unique=True)
    branch = models.ForeignKey(
        'branches.Branch',
        verbose_name='Филиал',
        related_name='employees',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    department = models.CharField('Отдел', max_length=150, blank=True)
    position = models.CharField('Должность', max_length=150, blank=True)
    hired_at = models.DateField('Дата найма', null=True, blank=True)
    salary = models.DecimalField('Оклад', max_digits=12, decimal_places=2, null=True, blank=True)
    status = models.CharField(
        'Статус', max_length=20, choices=EmployeeStatus.choices, default=EmployeeStatus.ACTIVE
    )

    class Meta:
        verbose_name = 'Профиль сотрудника'
        verbose_name_plural = 'Профили сотрудников'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['status'])]

    def __str__(self) -> str:
        return f'{self.employee_code} — {self.user}'


class DriverProfile(BaseModel):
    """Профиль водителя (ТЗ, раздел 02). Привязка к автомобилю добавится
    миграцией вместе с модулем vehicles (Этап 1, фаза B)."""

    user = models.OneToOneField(
        User, verbose_name='Пользователь', related_name='driver_profile', on_delete=models.CASCADE
    )
    driver_license = models.CharField('Водительское удостоверение', max_length=50, blank=True)
    license_expiry_date = models.DateField('Срок действия ВУ', null=True, blank=True)
    medical_certificate = models.CharField('Медицинская справка', max_length=100, blank=True)
    experience_years = models.PositiveSmallIntegerField('Стаж, лет', default=0)
    rating = models.DecimalField('Рейтинг', max_digits=3, decimal_places=2, default=0)
    status = models.CharField(
        'Статус', max_length=20, choices=DriverStatus.choices, default=DriverStatus.AVAILABLE
    )

    class Meta:
        verbose_name = 'Профиль водителя'
        verbose_name_plural = 'Профили водителей'
        ordering = ('-created_at',)
        indexes = [models.Index(fields=['status'])]

    def __str__(self) -> str:
        return f'Водитель {self.user}'


class DeviceSession(BaseModel):
    """Сессия устройства (ТЗ, разделы 13–14, 30): создаётся при каждом входе,
    хранит привязку к refresh-токену для точечного завершения."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Пользователь',
        related_name='device_sessions',
        on_delete=models.CASCADE,
    )
    refresh_jti = models.CharField('JTI refresh-токена', max_length=64, db_index=True)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=512, blank=True)
    login_at = models.DateTimeField('Вход', auto_now_add=True)
    last_activity = models.DateTimeField('Последняя активность', auto_now=True)

    class Meta:
        verbose_name = 'Сессия устройства'
        verbose_name_plural = 'Сессии устройств'
        ordering = ('-login_at',)
        indexes = [models.Index(fields=['user', 'is_active'])]

    def __str__(self) -> str:
        return f'{self.user} @ {self.ip or "-"}'
