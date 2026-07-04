import pytest
from django.urls import reverse

from apps.accounts.constants import Roles
from apps.accounts.models import User
from apps.accounts.tests.factories import UserFactory
from apps.branches.tests.factories import BranchFactory

pytestmark = pytest.mark.django_db

LIST_URL = reverse('users-list')


def detail_url(user_id) -> str:
    return reverse('users-detail', args=[user_id])


class TestUserCreate:
    def test_admin_creates_user(self, auth_client, admin_user):
        branch = BranchFactory()
        payload = {
            'phone': '+996700999001',
            'password': 'Emp1oyee-Pass!',
            'role': Roles.OPERATOR,
            'last_name': 'Асанов',
            'first_name': 'Бакыт',
            'branch': str(branch.id),
        }

        response = auth_client(admin_user).post(LIST_URL, payload)

        assert response.status_code == 201
        assert response.data['phone'] == payload['phone']
        assert response.data['branch']['id'] == str(branch.id)
        created = User.objects.get(phone=payload['phone'])
        assert created.check_password(payload['password'])

    def test_operator_cannot_create_user(self, auth_client, operator_user):
        response = auth_client(operator_user).post(LIST_URL, {'phone': '+996700999002'})

        assert response.status_code == 403
        assert response.data['error']['code'] == 'permission_denied'

    def test_duplicate_phone_returns_validation_error(self, auth_client, admin_user):
        existing = UserFactory()
        payload = {'phone': existing.phone, 'password': 'Emp1oyee-Pass!', 'role': Roles.OPERATOR}

        response = auth_client(admin_user).post(LIST_URL, payload)

        assert response.status_code == 400
        assert response.data['error']['code'] == 'validation_error'

    def test_weak_password_rejected(self, auth_client, admin_user):
        payload = {'phone': '+996700999003', 'password': '123', 'role': Roles.OPERATOR}

        response = auth_client(admin_user).post(LIST_URL, payload)

        assert response.status_code == 400
        assert response.data['error']['code'] == 'validation_error'


class TestUserListAndFilter:
    def test_list_filtered_by_role(self, auth_client, admin_user):
        UserFactory.create_batch(2, role=Roles.COURIER)
        UserFactory(role=Roles.FINANCE)

        response = auth_client(admin_user).get(LIST_URL, {'role': Roles.COURIER})

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_manager_has_access(self, auth_client, manager_user):
        response = auth_client(manager_user).get(LIST_URL)

        assert response.status_code == 200


class TestUserUpdateAndDeactivate:
    def test_admin_updates_role_and_branch(self, auth_client, admin_user):
        user = UserFactory(role=Roles.OPERATOR)
        branch = BranchFactory()

        response = auth_client(admin_user).patch(
            detail_url(user.id), {'role': Roles.MANAGER, 'branch': str(branch.id)}
        )

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.role == Roles.MANAGER
        assert user.branch == branch

    def test_destroy_deactivates_instead_of_delete(self, auth_client, admin_user):
        user = UserFactory()

        response = auth_client(admin_user).delete(detail_url(user.id))

        assert response.status_code == 204
        user.refresh_from_db()
        assert user.is_active is False
