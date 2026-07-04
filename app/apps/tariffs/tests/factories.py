import factory

from apps.tariffs.models import AdditionalService, Tariff


class TariffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tariff

    name = factory.Sequence(lambda n: f'Тариф {n}')
    code = factory.Sequence(lambda n: f'TRF{n:03d}')
    base_price = 200
    price_per_kg = 50
    price_per_m3 = 1000
    min_price = 0
    insurance_percent = 0


class AdditionalServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AdditionalService

    name = factory.Sequence(lambda n: f'Услуга {n}')
    code = factory.Sequence(lambda n: f'SRV{n:03d}')
    price = 100
