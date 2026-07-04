import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.users.choices import Roles
from apps.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _clear_cache():
    """Кэш (brute-force счётчики, throttle) не должен утекать между тестами."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def superadmin():
    return UserFactory(role=Roles.SUPERADMIN)


@pytest.fixture
def director():
    return UserFactory(role=Roles.DIRECTOR)


@pytest.fixture
def operator():
    return UserFactory(role=Roles.OPERATOR)


@pytest.fixture
def warehouse_user():
    return UserFactory(role=Roles.WAREHOUSE)


@pytest.fixture
def driver():
    return UserFactory(role=Roles.DRIVER)


@pytest.fixture
def finance_user():
    return UserFactory(role=Roles.FINANCE)


@pytest.fixture
def client_user():
    return UserFactory(role=Roles.CLIENT)


@pytest.fixture
def auth_client():
    """Фабрика аутентифицированных клиентов: client = auth_client(user)."""

    def _make(user) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _make
