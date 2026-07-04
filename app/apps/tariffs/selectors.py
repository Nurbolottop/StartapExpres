"""Селекторы tariffs: только чтение."""

from django.db.models import QuerySet

from apps.tariffs.models import AdditionalService, Tariff


class TariffSelector:
    @staticmethod
    def list() -> QuerySet[Tariff]:
        return Tariff.objects.select_related('from_city', 'to_city')

    @staticmethod
    def services() -> QuerySet[AdditionalService]:
        return AdditionalService.objects.all()
