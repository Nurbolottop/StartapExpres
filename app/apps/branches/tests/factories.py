import factory

from apps.branches.models import Branch


class BranchFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Branch

    name = factory.Sequence(lambda n: f'Филиал {n}')
    code = factory.Sequence(lambda n: f'BR{n:03d}')
    city = 'Бишкек'
    address = 'ул. Киевская, 1'
    is_active = True
