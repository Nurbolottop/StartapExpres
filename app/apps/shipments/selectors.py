"""Селекторы shipments: водитель видит только свои рейсы (ТЗ, раздел 14)."""

from django.db.models import QuerySet

from apps.shipments.models import Shipment
from apps.users.choices import Roles


class ShipmentSelector:
    @staticmethod
    def base() -> QuerySet[Shipment]:
        return Shipment.objects.select_related(
            'vehicle', 'driver', 'route', 'departure_branch', 'arrival_branch'
        ).prefetch_related('items__order', 'items__package')

    @classmethod
    def for_user(cls, user) -> QuerySet[Shipment]:
        queryset = cls.base()
        if user.role == Roles.DRIVER:
            return queryset.filter(driver=user)
        if user.role == Roles.CLIENT:
            return queryset.none()
        return queryset
