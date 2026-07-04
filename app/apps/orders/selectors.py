"""Селекторы orders: чтение со скоупингом по ролям (ТЗ, раздел 14: Ownership)."""

from django.db.models import QuerySet

from apps.orders.models import Order
from apps.users.choices import Roles


class OrderSelector:
    @staticmethod
    def base() -> QuerySet[Order]:
        return Order.objects.select_related('client', 'from_branch', 'to_branch', 'tariff').prefetch_related(
            'packages', 'service_items__service'
        )

    @classmethod
    def for_user(cls, user) -> QuerySet[Order]:
        """Client — только свои заказы; Driver — заказы в перевозке (после
        появления рейсов на Этапе 4 — только назначенные ему); остальные — все."""
        queryset = cls.base()
        if user.role == Roles.CLIENT:
            return queryset.filter(client=user)
        if user.role == Roles.DRIVER:
            return queryset.filter(shipment_items__shipment__driver=user).distinct()
        return queryset
