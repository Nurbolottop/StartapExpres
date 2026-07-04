"""Селекторы vehicles: только чтение."""

from django.db.models import QuerySet

from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle, VehicleType


class VehicleTypeSelector:
    @staticmethod
    def list() -> QuerySet[VehicleType]:
        return VehicleType.objects.all()


class VehicleSelector:
    @staticmethod
    def list() -> QuerySet[Vehicle]:
        return Vehicle.objects.select_related('vehicle_type', 'branch', 'current_driver')

    @staticmethod
    def available() -> QuerySet[Vehicle]:
        return VehicleSelector.list().filter(status=VehicleStatus.AVAILABLE, is_active=True)
