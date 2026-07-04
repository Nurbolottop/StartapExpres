import pytest
from django.urls import reverse

from apps.accounts.tests.factories import UserFactory
from apps.branches.models import Branch
from apps.branches.tests.factories import BranchFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse('branches-list')


def detail_url(branch_id) -> str:
    return reverse('branches-detail', args=[branch_id])


class TestBranchRead:
    def test_requires_authentication(self, api_client):
        response = api_client.get(LIST_URL)

        assert response.status_code == 401

    def test_any_authenticated_user_can_list(self, auth_client, operator_user):
        BranchFactory.create_batch(3)

        response = auth_client(operator_user).get(LIST_URL)

        assert response.status_code == 200
        assert response.data['count'] == 3

    def test_search_by_code(self, auth_client, operator_user):
        BranchFactory(name='Бишкек Центральный', code='BSH')
        BranchFactory(name='Ош Южный', code='OSH')

        response = auth_client(operator_user).get(LIST_URL, {'search': 'OSH'})

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['code'] == 'OSH'


class TestBranchWrite:
    def test_manager_creates_branch(self, auth_client, manager_user):
        payload = {'name': 'Каракол', 'code': 'KRK', 'city': 'Каракол'}

        response = auth_client(manager_user).post(LIST_URL, payload)

        assert response.status_code == 201
        assert Branch.objects.filter(code='KRK').exists()

    def test_operator_cannot_create_branch(self, auth_client, operator_user):
        response = auth_client(operator_user).post(LIST_URL, {'name': 'X', 'code': 'XX', 'city': 'X'})

        assert response.status_code == 403
        assert response.data['error']['code'] == 'permission_denied'

    def test_duplicate_code_rejected(self, auth_client, manager_user):
        BranchFactory(code='BSH')

        response = auth_client(manager_user).post(
            LIST_URL, {'name': 'Дубль', 'code': 'BSH', 'city': 'Бишкек'}
        )

        assert response.status_code == 400
        assert response.data['error']['code'] == 'validation_error'

    def test_lowercase_code_rejected(self, auth_client, manager_user):
        response = auth_client(manager_user).post(
            LIST_URL, {'name': 'Нарын', 'code': 'nrn', 'city': 'Нарын'}
        )

        assert response.status_code == 400


class TestBranchDelete:
    def test_delete_unused_branch(self, auth_client, admin_user):
        branch = BranchFactory()

        response = auth_client(admin_user).delete(detail_url(branch.id))

        assert response.status_code == 204
        assert not Branch.objects.filter(id=branch.id).exists()

    def test_delete_branch_with_users_returns_conflict(self, auth_client, admin_user):
        branch = BranchFactory()
        UserFactory(branch=branch)

        response = auth_client(admin_user).delete(detail_url(branch.id))

        assert response.status_code == 409
        assert response.data['error']['code'] == 'protected_object'
