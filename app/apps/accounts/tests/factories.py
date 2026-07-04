import factory

from apps.accounts.constants import Roles
from apps.accounts.models import User

DEFAULT_PASSWORD = 'Str0ngPass!2026'


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    phone = factory.Sequence(lambda n: f'+9967001{n:05d}')
    last_name = 'Тестов'
    first_name = 'Иван'
    role = Roles.OPERATOR
    is_active = True
    password = factory.django.Password(DEFAULT_PASSWORD)
