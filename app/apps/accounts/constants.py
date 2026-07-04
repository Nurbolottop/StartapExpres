from django.db import models


class Roles(models.TextChoices):
    CLIENT = 'client', 'Клиент'
    OPERATOR = 'operator', 'Оператор'
    WAREHOUSE = 'warehouse', 'Сотрудник склада'
    COURIER = 'courier', 'Водитель / курьер'
    FINANCE = 'finance', 'Финансист'
    MANAGER = 'manager', 'Руководитель'
    ADMIN = 'admin', 'Администратор'


STAFF_ROLES = (
    Roles.OPERATOR,
    Roles.WAREHOUSE,
    Roles.COURIER,
    Roles.FINANCE,
    Roles.MANAGER,
    Roles.ADMIN,
)
