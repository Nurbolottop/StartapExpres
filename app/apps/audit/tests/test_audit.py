import pytest
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.branches.tests.factories import CityFactory
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

AUDIT_URL = reverse('audit-list')


class TestAuditSubscriber:
    def test_domain_event_creates_audit_record(self, auth_client, superadmin):
        city = CityFactory()

        auth_client(superadmin).patch(reverse('cities-detail', args=[city.id]), {'name': 'Новое имя'})

        record = AuditLog.objects.filter(event_type='city.updated').first()
        assert record is not None
        assert record.user == superadmin
        assert record.role == superadmin.role
        assert record.old_data['name'] == city.name
        assert record.new_data['name'] == 'Новое имя'
        assert record.request_id


class TestAuditImmutability:
    def test_update_forbidden(self, superadmin):
        record = AuditLog.objects.create(user=superadmin, model='User', action='test')

        record.action = 'changed'
        with pytest.raises(ValueError):
            record.save()

    def test_delete_forbidden(self, superadmin):
        record = AuditLog.objects.create(user=superadmin, model='User', action='test')

        with pytest.raises(ValueError):
            record.delete()


class TestAuditAPI:
    def test_director_can_view_audit(self, auth_client, director):
        UserFactory()  # событие user не создаётся фабрикой, но журнал доступен

        response = auth_client(director).get(AUDIT_URL)

        assert response.status_code == 200

    def test_operator_cannot_view_audit(self, auth_client, operator):
        response = auth_client(operator).get(AUDIT_URL)

        assert response.status_code == 403

    def test_filter_by_action(self, auth_client, superadmin, api_client):
        from apps.users.tests.factories import DEFAULT_PASSWORD

        user = UserFactory()
        api_client.post(reverse('auth-login'), {'phone': user.phone, 'password': DEFAULT_PASSWORD})

        response = auth_client(superadmin).get(AUDIT_URL, {'action': 'login'})
        body = response.json()

        assert response.status_code == 200
        assert body['meta']['total'] >= 1
