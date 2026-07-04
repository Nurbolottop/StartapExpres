import pytest
from django.urls import reverse

from apps.accounts.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

LOGIN_URL = reverse('auth-login')
REFRESH_URL = reverse('auth-refresh')
LOGOUT_URL = reverse('auth-logout')
ME_URL = reverse('auth-me')
PASSWORD_CHANGE_URL = reverse('auth-password-change')


class TestLogin:
    def test_login_success_returns_tokens_and_user(self, api_client):
        user = UserFactory()

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        assert response.status_code == 200
        assert response.data['access']
        assert response.data['refresh']
        assert response.data['user']['phone'] == user.phone

    def test_login_wrong_password_returns_error_envelope(self, api_client):
        user = UserFactory()

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': 'wrong'})

        assert response.status_code == 401
        assert 'error' in response.data
        assert response.data['error']['code']

    def test_login_inactive_user_denied(self, api_client):
        user = UserFactory(is_active=False)

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        assert response.status_code == 401


class TestTokens:
    def test_refresh_returns_new_access(self, api_client):
        user = UserFactory()
        login = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        response = api_client.post(REFRESH_URL, {'refresh': login.data['refresh']})

        assert response.status_code == 200
        assert response.data['access']

    def test_logout_blacklists_refresh_token(self, api_client, auth_client):
        user = UserFactory()
        login = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})
        refresh = login.data['refresh']

        client = auth_client(user)
        logout = client.post(LOGOUT_URL, {'refresh': refresh})
        reuse = api_client.post(REFRESH_URL, {'refresh': refresh})

        assert logout.status_code == 204
        assert reuse.status_code == 401


class TestMe:
    def test_me_requires_authentication(self, api_client):
        response = api_client.get(ME_URL)

        assert response.status_code == 401
        assert 'error' in response.data

    def test_me_returns_profile(self, auth_client):
        user = UserFactory()

        response = auth_client(user).get(ME_URL)

        assert response.status_code == 200
        assert response.data['id'] == str(user.id)
        assert response.data['role'] == user.role

    def test_me_patch_updates_profile_fields(self, auth_client):
        user = UserFactory()

        response = auth_client(user).patch(ME_URL, {'first_name': 'Азамат', 'email': 'a@b.kg'})

        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == 'Азамат'
        assert user.email == 'a@b.kg'


class TestPasswordChange:
    def test_change_password_success(self, api_client, auth_client):
        user = UserFactory()
        new_password = 'N3w-Sup3r-Pass!'

        response = auth_client(user).post(
            PASSWORD_CHANGE_URL,
            {'old_password': DEFAULT_PASSWORD, 'new_password': new_password},
        )
        relogin = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': new_password})

        assert response.status_code == 204
        assert relogin.status_code == 200

    def test_change_password_wrong_old_password(self, auth_client):
        user = UserFactory()

        response = auth_client(user).post(
            PASSWORD_CHANGE_URL,
            {'old_password': 'wrong', 'new_password': 'N3w-Sup3r-Pass!'},
        )

        assert response.status_code == 400
        assert response.data['error']['code'] == 'invalid_password'
