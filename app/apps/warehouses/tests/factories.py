import factory

from apps.branches.tests.factories import BranchFactory
from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone


class WarehouseFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Warehouse

    branch = factory.SubFactory(BranchFactory)
    name = factory.Sequence(lambda n: f'Склад {n}')
    code = factory.Sequence(lambda n: f'WH{n:03d}')


class ZoneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WarehouseZone

    warehouse = factory.SubFactory(WarehouseFactory)
    name = factory.Sequence(lambda n: f'Зона {n}')
    code = factory.Sequence(lambda n: f'Z{n:02d}')


class CellFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WarehouseCell

    zone = factory.SubFactory(ZoneFactory)
    code = factory.Sequence(lambda n: f'C{n:03d}')
    capacity_weight = 500
    capacity_volume = 5
