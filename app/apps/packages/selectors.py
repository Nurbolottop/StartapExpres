"""Селекторы packages: чтение со скоупингом клиента."""

from django.db.models import QuerySet

from apps.packages.models import Package
from apps.users.choices import Roles


class PackageSelector:
    @staticmethod
    def base() -> QuerySet[Package]:
        return Package.objects.select_related('order__client')

    @classmethod
    def for_user(cls, user) -> QuerySet[Package]:
        queryset = cls.base()
        if user.role == Roles.CLIENT:
            return queryset.filter(order__client=user)
        if user.role == Roles.DRIVER:
            return queryset.none()
        return queryset
