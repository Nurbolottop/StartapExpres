import factory

from apps.users.choices import Roles
from apps.users.models import User
from apps.users.services import UserService

DEFAULT_PASSWORD = 'Str0ng!Passw0rd#26'


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

    @factory.post_generation
    def profile(user, create, extracted, **kwargs):
        if create:
            UserService.create_profile(user)
