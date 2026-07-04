from django.db import models


class VehicleStatus(models.TextChoices):
    AVAILABLE = 'available', 'Свободен'
    BUSY = 'busy', 'В рейсе'
    MAINTENANCE = 'maintenance', 'На обслуживании'
    INACTIVE = 'inactive', 'Не используется'


class FuelType(models.TextChoices):
    PETROL = 'petrol', 'Бензин'
    DIESEL = 'diesel', 'Дизель'
    GAS = 'gas', 'Газ'
    ELECTRIC = 'electric', 'Электро'
    HYBRID = 'hybrid', 'Гибрид'
