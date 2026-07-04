import pytest
from rest_framework.test import APIClient

from apps.accounts.constants import Roles
from apps.accounts.tests.factories import UserFactory


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_user():
    return UserFactory(role=Roles.ADMIN)


@pytest.fixture
def manager_user():
    return UserFactory(role=Roles.MANAGER)


@pytest.fixture
def operator_user():
    return UserFactory(role=Roles.OPERATOR)


@pytest.fixture
def auth_client():
    """Фабрика аутентифицированных клиентов: client = auth_client(user)."""

    def _make(user) -> APIClient:
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _make
