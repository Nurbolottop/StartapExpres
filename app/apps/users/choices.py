from django.db import models


class Roles(models.TextChoices):
    CLIENT = 'client', 'Клиент'
    OPERATOR = 'operator', 'Оператор'
    WAREHOUSE = 'warehouse', 'Сотрудник склада'
    DRIVER = 'driver', 'Водитель'
    FINANCE = 'finance', 'Финансист'
    DIRECTOR = 'director', 'Директор'
    SUPERADMIN = 'superadmin', 'Суперадминистратор'


STAFF_ROLES = (
    Roles.OPERATOR,
    Roles.WAREHOUSE,
    Roles.FINANCE,
    Roles.DIRECTOR,
    Roles.SUPERADMIN,
)

MANAGEMENT_ROLES = (Roles.DIRECTOR, Roles.SUPERADMIN)


class Languages(models.TextChoices):
    KYRGYZ = 'ky', 'Кыргызча'
    RUSSIAN = 'ru', 'Русский'
    ENGLISH = 'en', 'English'


class EmployeeStatus(models.TextChoices):
    ACTIVE = 'active', 'Работает'
    VACATION = 'vacation', 'В отпуске'
    SUSPENDED = 'suspended', 'Отстранён'
    FIRED = 'fired', 'Уволен'


class DriverStatus(models.TextChoices):
    AVAILABLE = 'available', 'Свободен'
    ON_TRIP = 'on_trip', 'В рейсе'
    DAY_OFF = 'day_off', 'Выходной'
    SUSPENDED = 'suspended', 'Отстранён'
