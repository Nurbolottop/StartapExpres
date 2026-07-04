import pytest
from django.urls import reverse

from apps.common.services import generate_number
from apps.users.models import ClientProfile
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestEnvelope:
    def test_health_wrapped_in_envelope_with_headers(self, api_client):
        response = api_client.get(reverse('health'))
        body = response.json()

        assert response.status_code == 200
        assert body['success'] is True
        assert body['data']['status'] == 'ok'
        assert response.headers['X-Request-ID']
        assert response.headers['X-Correlation-ID']
        assert response.headers['X-API-Version'] == 'v1'
        assert 'ms' in response.headers['X-Execution-Time']

    def test_correlation_id_passthrough(self, api_client):
        response = api_client.get(reverse('health'), HTTP_X_CORRELATION_ID='corr-123')

        assert response.headers['X-Correlation-ID'] == 'corr-123'

    def test_error_envelope_format(self, api_client):
        response = api_client.get(reverse('users-list'))
        body = response.json()

        assert response.status_code == 401
        assert body['success'] is False
        assert 'code' in body['error']


class TestHealthEndpoints:
    @pytest.mark.parametrize('name', ['health-db', 'health-cache', 'health-redis'])
    def test_component_health(self, api_client, name):
        response = api_client.get(reverse(name))
        body = response.json()

        assert response.status_code == 200
        assert body['data']['status'] == 'ok'


class TestNumberSequence:
    def test_yearly_format_and_increment(self):
        first = generate_number('ORD')
        second = generate_number('ORD')

        prefix, year, number = first.split('-')
        assert prefix == 'ORD'
        assert len(number) == 6
        assert int(second.split('-')[2]) == int(number) + 1

    def test_scopes_are_independent(self):
        generate_number('SHP')
        first_inv = generate_number('INV')

        assert first_inv.split('-')[2] == '000001'


class TestEncryptedField:
    def test_passport_stored_encrypted_but_read_plain(self, client_user):
        profile = ClientProfile.objects.get(user=client_user)
        profile.passport_number = 'AN1234567'
        profile.save()

        profile.refresh_from_db()
        assert profile.passport_number == 'AN1234567'

        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT passport_number FROM users_clientprofile WHERE client_code = %s',
                [profile.client_code],
            )
            stored = cursor.fetchone()[0]
        assert stored != 'AN1234567'
        assert stored.startswith('enc:')


class TestSoftDelete:
    def test_soft_delete_and_hard_delete(self):
        user = UserFactory()
        user.delete()

        from apps.users.models import User

        assert not User.objects.filter(id=user.id).exists()
        assert User.all_objects.filter(id=user.id).exists()

        user.hard_delete()
        assert not User.all_objects.filter(id=user.id).exists()
