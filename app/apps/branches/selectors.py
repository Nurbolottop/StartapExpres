"""Селекторы branches: только чтение."""

from django.db.models import QuerySet

from apps.branches.models import Branch, City


class CitySelector:
    @staticmethod
    def list() -> QuerySet[City]:
        return City.objects.all()


class BranchSelector:
    @staticmethod
    def list() -> QuerySet[Branch]:
        return Branch.objects.select_related('city')
