import factory

from apps.vehicles.models import Vehicle, VehicleType


class VehicleTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = VehicleType

    name = factory.Sequence(lambda n: f'Фургон {n}')
    code = factory.Sequence(lambda n: f'VT{n:03d}')
    max_weight = 3000
    max_volume = 20


class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicle

    vehicle_type = factory.SubFactory(VehicleTypeFactory)
    plate_number = factory.Sequence(lambda n: f'01KG{n:04d}AB')
    brand = 'Mercedes'
    model = 'Sprinter'
    max_weight = 3000
    max_volume = 20
