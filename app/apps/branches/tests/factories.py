import factory

from apps.branches.models import Branch, City


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = City

    name = factory.Sequence(lambda n: f'Город {n}')
    code = factory.Sequence(lambda n: f'CT{n:03d}')
    country = 'Кыргызстан'


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch

    city = factory.SubFactory(CityFactory)
    name = factory.Sequence(lambda n: f'Филиал {n}')
    code = factory.Sequence(lambda n: f'BR{n:03d}')
    address = 'ул. Киевская, 1'
