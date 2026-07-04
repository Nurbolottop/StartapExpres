import pytest
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.users.models import ClientProfile, DeviceSession, User
from apps.users.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

REGISTER_URL = reverse('auth-register')
LOGIN_URL = reverse('auth-login')
REFRESH_URL = reverse('auth-refresh')
LOGOUT_URL = reverse('auth-logout')
LOGOUT_ALL_URL = reverse('auth-logout-all')
ME_URL = reverse('auth-me')
CHANGE_PASSWORD_URL = reverse('auth-change-password')
SESSIONS_URL = reverse('auth-sessions')


class TestRegister:
    def test_register_creates_client_with_profile_and_tokens(self, api_client):
        payload = {
            'phone': '+996700111222',
            'password': DEFAULT_PASSWORD,
            'first_name': 'Айбек',
            'last_name': 'Асанов',
        }

        response = api_client.post(REGISTER_URL, payload)
        body = response.json()

        assert response.status_code == 201
        assert body['success'] is True
        assert body['data']['access'] and body['data']['refresh']
        assert body['data']['user']['role'] == 'client'
        user = User.objects.get(phone=payload['phone'])
        profile = ClientProfile.objects.get(user=user)
        assert profile.client_code.startswith('CLT-')
        assert DeviceSession.objects.filter(user=user, is_active=True).count() == 1

    def test_register_weak_password_rejected(self, api_client):
        response = api_client.post(REGISTER_URL, {'phone': '+996700111223', 'password': '123'})
        body = response.json()

        assert response.status_code == 400
        assert body['success'] is False
        assert body['error']['code'] == 'VALIDATION_ERROR'

    def test_register_duplicate_phone_rejected(self, api_client):
        existing = UserFactory()

        response = api_client.post(REGISTER_URL, {'phone': existing.phone, 'password': DEFAULT_PASSWORD})

        assert response.status_code == 400
        assert response.json()['error']['code'] == 'VALIDATION_ERROR'


class TestLogin:
    def test_login_success_returns_envelope_with_tokens(self, api_client):
        user = UserFactory()

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})
        body = response.json()

        assert response.status_code == 200
        assert body['success'] is True
        assert body['data']['user']['phone'] == user.phone
        user.refresh_from_db()
        assert user.last_login is not None
        assert DeviceSession.objects.filter(user=user, is_active=True).exists()

    def test_login_wrong_password_returns_auth_error(self, api_client):
        user = UserFactory()

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': 'wrong'})
        body = response.json()

        assert response.status_code == 401
        assert body['success'] is False
        assert body['error']['code'] == 'AUTH_002'

    def test_login_blocked_after_five_failures(self, api_client):
        user = UserFactory()
        for _ in range(5):
            api_client.post(LOGIN_URL, {'phone': user.phone, 'password': 'wrong'})

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        assert response.status_code == 429
        assert response.json()['error']['code'] == 'AUTH_006'

    def test_login_inactive_user_returns_blocked(self, api_client):
        user = UserFactory(is_active=False)

        response = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        assert response.status_code == 403
        assert response.json()['error']['code'] == 'AUTH_005'

    def test_login_writes_audit_log(self, api_client):
        user = UserFactory()

        api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        assert AuditLog.objects.filter(user=user, event_type='user.logged_in').exists()


class TestTokens:
    def test_refresh_rotates_and_keeps_session_terminable(self, api_client):
        user = UserFactory()
        login = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD}).json()

        refreshed = api_client.post(REFRESH_URL, {'refresh': login['data']['refresh']}).json()

        assert refreshed['success'] is True
        assert refreshed['data']['access']
        # сессия перепривязана к новому jti
        session = DeviceSession.objects.get(user=user, is_active=True)
        old_reuse = api_client.post(REFRESH_URL, {'refresh': login['data']['refresh']})
        assert old_reuse.status_code == 401
        assert session.refresh_jti

    def test_logout_blacklists_and_closes_session(self, api_client, auth_client):
        user = UserFactory()
        login = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD}).json()
        refresh = login['data']['refresh']

        logout = auth_client(user).post(LOGOUT_URL, {'refresh': refresh})
        reuse = api_client.post(REFRESH_URL, {'refresh': refresh})

        assert logout.status_code == 204
        assert reuse.status_code == 401
        assert not DeviceSession.objects.filter(user=user, is_active=True).exists()

    def test_logout_all_closes_every_session(self, api_client, auth_client):
        user = UserFactory()
        first = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD}).json()
        api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD})
        assert DeviceSession.objects.filter(user=user, is_active=True).count() == 2

        response = auth_client(user).post(LOGOUT_ALL_URL)
        reuse = api_client.post(REFRESH_URL, {'refresh': first['data']['refresh']})

        assert response.status_code == 204
        assert reuse.status_code == 401
        assert not DeviceSession.objects.filter(user=user, is_active=True).exists()


class TestMe:
    def test_me_requires_authentication(self, api_client):
        response = api_client.get(ME_URL)
        body = response.json()

        assert response.status_code == 401
        assert body['success'] is False

    def test_me_returns_profile(self, auth_client, client_user):
        response = auth_client(client_user).get(ME_URL)
        body = response.json()

        assert response.status_code == 200
        assert body['data']['id'] == str(client_user.id)
        assert body['data']['profile']['client_code'].startswith('CLT-')

    def test_me_patch_updates_allowed_fields(self, auth_client, operator):
        response = auth_client(operator).patch(ME_URL, {'first_name': 'Азамат', 'language': 'ky'})

        assert response.status_code == 200
        operator.refresh_from_db()
        assert operator.first_name == 'Азамат'
        assert operator.language == 'ky'


class TestPasswordChange:
    def test_change_password_success(self, api_client, auth_client):
        user = UserFactory()
        new_password = 'N3w!Sup3r#Passw0rd'

        response = auth_client(user).post(
            CHANGE_PASSWORD_URL,
            {'old_password': DEFAULT_PASSWORD, 'new_password': new_password},
        )
        relogin = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': new_password})

        assert response.status_code == 204
        assert relogin.status_code == 200

    def test_change_password_wrong_old(self, auth_client, operator):
        response = auth_client(operator).post(
            CHANGE_PASSWORD_URL, {'old_password': 'wrong', 'new_password': 'N3w!Sup3r#Passw0rd'}
        )

        assert response.status_code == 401
        assert response.json()['error']['code'] == 'AUTH_002'

    def test_change_password_too_simple_rejected(self, auth_client, operator):
        response = auth_client(operator).post(
            CHANGE_PASSWORD_URL, {'old_password': DEFAULT_PASSWORD, 'new_password': 'short'}
        )

        assert response.status_code == 400
        assert response.json()['error']['code'] == 'VALIDATION_ERROR'


class TestSessions:
    def test_sessions_list_and_terminate(self, api_client):
        user = UserFactory()
        login = api_client.post(LOGIN_URL, {'phone': user.phone, 'password': DEFAULT_PASSWORD}).json()
        access = login['data']['access']
        refresh = login['data']['refresh']

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        sessions = api_client.get(SESSIONS_URL).json()
        assert len(sessions['data']) == 1

        session_id = sessions['data'][0]['id']
        response = api_client.delete(reverse('auth-session-terminate', args=[session_id]))
        api_client.credentials()
        reuse = api_client.post(REFRESH_URL, {'refresh': refresh})

        assert response.status_code == 204
        assert reuse.status_code == 401
