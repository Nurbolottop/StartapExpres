import pytest
from django.urls import reverse

from apps.users import exceptions
from apps.users.choices import Roles
from apps.users.models import DriverProfile, EmployeeProfile, User
from apps.users.services import UserService
from apps.users.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

USERS_URL = reverse('users-list')
CLIENTS_URL = reverse('clients-list')


def user_url(user_id) -> str:
    return reverse('users-detail', args=[user_id])


class TestUserCreate:
    def test_superadmin_creates_employee_with_profile(self, auth_client, superadmin):
        payload = {
            'phone': '+996700222333',
            'password': DEFAULT_PASSWORD,
            'role': Roles.OPERATOR,
            'first_name': 'Бакыт',
            'position': 'Старший оператор',
        }

        response = auth_client(superadmin).post(USERS_URL, payload)
        body = response.json()

        assert response.status_code == 201
        created = User.objects.get(phone=payload['phone'])
        profile = EmployeeProfile.objects.get(user=created)
        assert profile.employee_code.startswith('EMP-')
        assert profile.position == 'Старший оператор'
        assert body['data']['profile']['employee_code'] == profile.employee_code

    def test_director_creates_driver_with_profile(self, auth_client, director):
        payload = {
            'phone': '+996700222334',
            'password': DEFAULT_PASSWORD,
            'role': Roles.DRIVER,
            'driver_license': 'AB123456',
        }

        response = auth_client(director).post(USERS_URL, payload)

        assert response.status_code == 201
        created = User.objects.get(phone=payload['phone'])
        assert DriverProfile.objects.get(user=created).driver_license == 'AB123456'

    def test_director_cannot_create_superadmin(self, auth_client, director):
        payload = {'phone': '+996700222335', 'password': DEFAULT_PASSWORD, 'role': Roles.SUPERADMIN}

        response = auth_client(director).post(USERS_URL, payload)

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'USER_006'

    def test_operator_creates_only_clients(self, auth_client, operator):
        ok = auth_client(operator).post(
            USERS_URL, {'phone': '+996700222336', 'password': DEFAULT_PASSWORD, 'role': Roles.CLIENT}
        )
        forbidden = auth_client(operator).post(
            USERS_URL, {'phone': '+996700222337', 'password': DEFAULT_PASSWORD, 'role': Roles.DRIVER}
        )

        assert ok.status_code == 201
        assert forbidden.status_code == 422
        assert forbidden.json()['error']['code'] == 'USER_006'

    def test_warehouse_cannot_access_users(self, auth_client, warehouse_user):
        response = auth_client(warehouse_user).get(USERS_URL)

        assert response.status_code == 403
        assert response.json()['error']['code'] == 'PERMISSION_DENIED'


class TestUserList:
    def test_finance_can_list_users(self, auth_client, finance_user):
        UserFactory.create_batch(2, role=Roles.DRIVER)

        response = auth_client(finance_user).get(USERS_URL, {'role': Roles.DRIVER})
        body = response.json()

        assert response.status_code == 200
        assert body['meta']['total'] == 2
        assert body['meta']['page'] == 1

    def test_client_cannot_list_users(self, auth_client, client_user):
        response = auth_client(client_user).get(USERS_URL)

        assert response.status_code == 403


class TestUserUpdateAndDelete:
    def test_role_change_creates_new_profile(self, auth_client, superadmin):
        user = UserFactory(role=Roles.OPERATOR)

        response = auth_client(superadmin).patch(user_url(user.id), {'role': Roles.DRIVER})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.role == Roles.DRIVER
        assert DriverProfile.objects.filter(user=user).exists()

    def test_cannot_deactivate_self(self, auth_client, superadmin):
        response = auth_client(superadmin).patch(user_url(superadmin.id), {'is_active': False})

        assert response.status_code == 409

    def test_soft_delete_hides_user_and_closes_sessions(self, auth_client, superadmin):
        user = UserFactory()

        response = auth_client(superadmin).delete(user_url(user.id))

        assert response.status_code == 204
        assert not User.objects.filter(id=user.id).exists()
        assert User.all_objects.filter(id=user.id, is_deleted=True).exists()

    def test_cannot_delete_last_superadmin(self, superadmin, director):
        director.is_superuser = True
        director.save(update_fields=['is_superuser'])

        with pytest.raises(exceptions.LastSuperAdminException):
            UserService.soft_delete(actor=director, user=superadmin)


class TestClientsEndpoint:
    def test_operator_lists_only_clients(self, auth_client, operator, client_user):
        UserFactory(role=Roles.DRIVER)

        response = auth_client(operator).get(CLIENTS_URL)
        body = response.json()

        assert response.status_code == 200
        assert body['meta']['total'] == 1
        assert body['data'][0]['role'] == Roles.CLIENT

    def test_operator_creates_client_with_company(self, auth_client, operator):
        payload = {
            'phone': '+996700333444',
            'password': DEFAULT_PASSWORD,
            'company_name': 'ОсОО Тез Доставка',
        }

        response = auth_client(operator).post(CLIENTS_URL, payload)
        body = response.json()

        assert response.status_code == 201
        assert body['data']['role'] == Roles.CLIENT
        assert body['data']['profile']['company_name'] == 'ОсОО Тез Доставка'

    def test_driver_cannot_access_clients(self, auth_client, driver):
        response = auth_client(driver).get(CLIENTS_URL)

        assert response.status_code == 403
