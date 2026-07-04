"""Сервисный слой tariffs: справочники тарифов/услуг и расчёт стоимости.

Формула (ТЗ, раздел 04):
    Стоимость = базовый тариф + вес + объём + доп. услуги + страховка
"""

from decimal import Decimal

from django.db import transaction

from apps.common import events
from apps.tariffs.exceptions import TariffNotFoundException
from apps.tariffs.models import AdditionalService, Tariff


class _CrudService:
    model: type
    event_prefix: str
    source = 'tariffs'

    @classmethod
    @transaction.atomic
    def create(cls, *, actor, data: dict):
        instance = cls.model(created_by=actor, **data)
        instance.full_clean()
        instance.save()
        events.publish(
            f'{cls.event_prefix}.created',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'create',
                'new': {'repr': str(instance)},
            },
            source=cls.source,
        )
        return instance

    @classmethod
    @transaction.atomic
    def update(cls, *, actor, instance, data: dict):
        old = {field: str(getattr(instance, field)) for field in data}
        for field, value in data.items():
            setattr(instance, field, value)
        instance.updated_by = actor
        instance.full_clean()
        instance.save()
        events.publish(
            f'{cls.event_prefix}.updated',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'update',
                'old': old,
                'new': {field: str(getattr(instance, field)) for field in old},
            },
            source=cls.source,
        )
        return instance

    @classmethod
    @transaction.atomic
    def soft_delete(cls, *, actor, instance) -> None:
        instance.updated_by = actor
        instance.is_active = False
        instance.save(update_fields=['updated_by', 'is_active', 'updated_at'])
        instance.delete()
        events.publish(
            f'{cls.event_prefix}.deleted',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'soft_delete',
            },
            source=cls.source,
        )


class AdditionalServiceService(_CrudService):
    model = AdditionalService
    event_prefix = 'additional_service'


class TariffService(_CrudService):
    model = Tariff
    event_prefix = 'tariff'

    @staticmethod
    def find_for_route(from_city, to_city) -> Tariff:
        """Точный тариф направления, иначе тариф по умолчанию (from/to = NULL)."""
        tariff = Tariff.objects.filter(from_city=from_city, to_city=to_city, is_active=True).first()
        if tariff is None:
            tariff = Tariff.objects.filter(
                from_city__isnull=True, to_city__isnull=True, is_active=True
            ).first()
        if tariff is None:
            raise TariffNotFoundException()
        return tariff

    @classmethod
    def calculate(
        cls,
        *,
        from_city,
        to_city,
        weight: Decimal,
        volume: Decimal,
        declared_value: Decimal = Decimal('0'),
        services: list[AdditionalService] | None = None,
    ) -> dict:
        """Расчёт стоимости доставки. Возвращает разбивку и итог."""
        tariff = cls.find_for_route(from_city, to_city)
        services = services or []

        weight_price = tariff.price_per_kg * weight
        volume_price = tariff.price_per_m3 * volume
        services_price = sum((service.price for service in services), Decimal('0'))
        insurance_price = declared_value * tariff.insurance_percent / Decimal('100')

        total = tariff.base_price + weight_price + volume_price + services_price + insurance_price
        total = max(total, tariff.min_price).quantize(Decimal('0.01'))

        return {
            'tariff': tariff,
            'base_price': tariff.base_price.quantize(Decimal('0.01')),
            'weight_price': weight_price.quantize(Decimal('0.01')),
            'volume_price': volume_price.quantize(Decimal('0.01')),
            'services_price': services_price.quantize(Decimal('0.01')),
            'insurance_price': insurance_price.quantize(Decimal('0.01')),
            'total_price': total,
        }
