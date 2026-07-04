import factory

from apps.branches.tests.factories import BranchFactory
from apps.common.services import generate_number
from apps.orders.models import Order
from apps.users.choices import Roles
from apps.users.tests.factories import UserFactory


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    order_number = factory.LazyFunction(lambda: generate_number('ORD'))
    client = factory.SubFactory(UserFactory, role=Roles.CLIENT)
    sender_name = 'Асан Асанов'
    sender_phone = '+996700111111'
    receiver_name = 'Болот Болотов'
    receiver_phone = '+996700222222'
    from_branch = factory.SubFactory(BranchFactory)
    to_branch = factory.SubFactory(BranchFactory)
    total_price = 1000
