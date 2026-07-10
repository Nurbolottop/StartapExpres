"""Тесты доработок для мобильного приложения: OTP (сброс пароля, верификация
телефона), регистрация push-устройств, локализация сообщений."""

import pytest
from django.urls import reverse

from apps.notifications.choices import NotificationType
from apps.notifications.models import Device, NotificationTemplate
from apps.users.choices import Roles
from apps.users.models import User
from apps.users.otp import (
    PURPOSE_PASSWORD_RESET,
    PURPOSE_PHONE_VERIFY,
    OTPService,
)
from apps.users.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db

RESET_REQUEST_URL = reverse('auth-password-reset-request')
RESET_CONFIRM_URL = reverse('auth-password-reset-confirm')
VERIFY_REQUEST_URL = reverse('auth-verify-request')
VERIFY_CONFIRM_URL = reverse('auth-verify-confirm')
DEVICES_URL = reverse('auth-devices')
LOGIN_URL = reverse('auth-login')

NEW_PASSWORD = 'N3w!Str0ngPass#26'


@pytest.fixture
def sms_templates():
    """SMS-шаблоны OTP (обычно приходят из data-миграции 0004)."""
    for name in ('auth.password_reset_code', 'auth.verify_code'):
        NotificationTemplate.objects.get_or_create(
            name=name,
            type=NotificationType.SMS,
            language='ru',
            defaults={'title': 'Код', 'body': 'Код: {{code}}'},
        )


class TestPasswordReset:
    def test_request_always_ok_even_for_unknown_phone(self, api_client):
        response = api_client.post(RESET_REQUEST_URL, {'phone': '+996700000000'})
        assert response.status_code == 200
        assert response.json()['success'] is True

    def test_request_creates_sms_notification(self, api_client, sms_templates):
        user = UserFactory(phone='+996700333400')
        api_client.post(RESET_REQUEST_URL, {'phone': user.phone})
        assert user.notifications.filter(type=NotificationType.SMS).exists()

    def test_full_reset_flow_changes_password(self, api_client):
        user = UserFactory(phone='+996700333444')
        code = OTPService.issue(phone=user.phone, purpose=PURPOSE_PASSWORD_RESET)  # известный код

        response = api_client.post(
            RESET_CONFIRM_URL,
            {'phone': user.phone, 'code': code, 'new_password': NEW_PASSWORD},
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)

    def test_confirm_wrong_code_returns_auth_007(self, api_client, sms_templates):
        user = UserFactory(phone='+996700333555')
        OTPService.issue(phone=user.phone, purpose=PURPOSE_PASSWORD_RESET)

        response = api_client.post(
            RESET_CONFIRM_URL,
            {'phone': user.phone, 'code': '000000', 'new_password': NEW_PASSWORD},
        )
        assert response.status_code == 400
        assert response.json()['error']['code'] == 'AUTH_007'

    def test_resend_within_cooldown_returns_auth_008(self, api_client, sms_templates):
        user = UserFactory(phone='+996700333666')
        first = api_client.post(RESET_REQUEST_URL, {'phone': user.phone})
        assert first.status_code == 200
        second = api_client.post(RESET_REQUEST_URL, {'phone': user.phone})
        assert second.status_code == 429
        assert second.json()['error']['code'] == 'AUTH_008'


class TestPhoneVerification:
    def test_verify_flow_sets_is_verified(self, api_client):
        user = UserFactory(phone='+996700444555', is_verified=False)
        code = OTPService.issue(phone=user.phone, purpose=PURPOSE_PHONE_VERIFY)

        response = api_client.post(VERIFY_CONFIRM_URL, {'phone': user.phone, 'code': code})
        assert response.status_code == 200
        assert response.json()['data']['is_verified'] is True
        user.refresh_from_db()
        assert user.is_verified is True


class TestDeviceRegistration:
    def test_register_device_creates_record(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)

        response = api_client.post(
            DEVICES_URL,
            {'fcm_token': 'tok-123', 'platform': 'android', 'device_id': 'dev-1'},
        )
        assert response.status_code == 201
        assert Device.objects.filter(user=user, device_id='dev-1', is_active=True).exists()

    def test_reregister_same_device_updates_token(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        api_client.post(DEVICES_URL, {'fcm_token': 'old', 'platform': 'android', 'device_id': 'dev-1'})
        api_client.post(DEVICES_URL, {'fcm_token': 'new', 'platform': 'android', 'device_id': 'dev-1'})

        assert Device.objects.filter(user=user, device_id='dev-1').count() == 1
        assert Device.objects.get(device_id='dev-1').fcm_token == 'new'

    def test_unregister_device(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        api_client.post(DEVICES_URL, {'fcm_token': 't', 'platform': 'ios', 'device_id': 'dev-2'})

        url = reverse('auth-device-unregister', kwargs={'device_id': 'dev-2'})
        response = api_client.delete(url)
        assert response.status_code == 204
        assert not Device.objects.filter(device_id='dev-2', is_active=True).exists()

    def test_device_ownership_isolated(self, api_client):
        owner = UserFactory()
        other = UserFactory()
        api_client.force_authenticate(owner)
        api_client.post(DEVICES_URL, {'fcm_token': 't', 'platform': 'ios', 'device_id': 'dev-3'})

        api_client.force_authenticate(other)
        url = reverse('auth-device-unregister', kwargs={'device_id': 'dev-3'})
        response = api_client.delete(url)
        assert response.status_code == 404


class TestSelfDelete:
    def test_delete_own_account_soft_deletes_and_anonymizes(self, api_client):
        user = UserFactory(phone='+996700888111', role=Roles.CLIENT, email='c@ex.com')
        api_client.force_authenticate(user)

        response = api_client.delete(reverse('auth-me'))
        assert response.status_code == 204

        deleted = User.all_objects.get(id=user.id)
        assert deleted.is_active is False
        assert deleted.is_deleted is True
        assert deleted.phone != '+996700888111'
        assert deleted.email is None
        assert deleted.first_name == ''

    def test_phone_freed_for_reregistration(self, api_client):
        user = UserFactory(phone='+996700888222', role=Roles.CLIENT)
        api_client.force_authenticate(user)
        api_client.delete(reverse('auth-me'))

        api_client.force_authenticate(user=None)
        response = api_client.post(
            reverse('auth-register'),
            {'phone': '+996700888222', 'password': DEFAULT_PASSWORD},
        )
        assert response.status_code == 201

    def test_last_superadmin_cannot_self_delete(self, api_client):
        admin = UserFactory(role=Roles.SUPERADMIN)
        api_client.force_authenticate(admin)
        response = api_client.delete(reverse('auth-me'))
        assert response.status_code == 409


class TestLocalization:
    def test_message_localized_by_accept_language(self, api_client):
        UserFactory(phone='+996700555666', password=DEFAULT_PASSWORD)

        # неверный пароль → сообщение об ошибке на выбранном языке
        en = api_client.post(
            LOGIN_URL, {'phone': '+996700555666', 'password': 'wrong'}, HTTP_ACCEPT_LANGUAGE='en'
        )
        ky = api_client.post(
            LOGIN_URL, {'phone': '+996700555666', 'password': 'wrong'}, HTTP_ACCEPT_LANGUAGE='ky'
        )
        assert en.json()['message'] == 'Invalid phone or password.'
        assert ky.json()['message'] != en.json()['message']
        assert en.json()['error']['code'] == 'AUTH_002'

    def test_success_message_localized(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user)
        response = api_client.get(reverse('auth-me'), HTTP_ACCEPT_LANGUAGE='en')
        assert response.json()['message'] == 'Success'
