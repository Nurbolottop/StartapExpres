import pytest
from django.urls import reverse

from apps.branches.models import Branch, City
from apps.branches.tests.factories import BranchFactory, CityFactory

pytestmark = pytest.mark.django_db

CITIES_URL = reverse('cities-list')
BRANCHES_URL = reverse('branches-list')


class TestCities:
    def test_requires_authentication(self, api_client):
        response = api_client.get(CITIES_URL)
        assert response.status_code == 401

    def test_superadmin_creates_city(self, auth_client, superadmin):
        response = auth_client(superadmin).post(
            CITIES_URL, {'name': 'Бишкек', 'code': 'BSH', 'latitude': '42.87', 'longitude': '74.59'}
        )

        assert response.status_code == 201
        assert City.objects.filter(code='BSH').exists()

    def test_operator_cannot_create_city(self, auth_client, operator):
        response = auth_client(operator).post(CITIES_URL, {'name': 'Ош', 'code': 'OSH'})

        assert response.status_code == 403


class TestBranches:
    def test_staff_lists_branches_with_meta(self, auth_client, operator):
        BranchFactory.create_batch(3)

        response = auth_client(operator).get(BRANCHES_URL)
        body = response.json()

        assert response.status_code == 200
        assert body['success'] is True
        assert body['meta']['total'] == 3

    def test_superadmin_creates_branch(self, auth_client, superadmin):
        city = CityFactory()
        payload = {
            'city': str(city.id),
            'name': 'Бишкек Центральный',
            'code': 'BSHC',
            'phone': '+996312900000',
        }

        response = auth_client(superadmin).post(BRANCHES_URL, payload)

        assert response.status_code == 201
        assert Branch.objects.filter(code='BSHC').exists()

    def test_duplicate_code_rejected(self, auth_client, superadmin):
        BranchFactory(code='BSH')
        city = CityFactory()

        response = auth_client(superadmin).post(
            BRANCHES_URL, {'city': str(city.id), 'name': 'Дубль', 'code': 'BSH'}
        )
        body = response.json()

        assert response.status_code == 400
        assert body['error']['code'] == 'VALIDATION_ERROR'
        assert 'code' in body['error']['fields']

    def test_soft_delete_hides_branch(self, auth_client, superadmin):
        branch = BranchFactory()

        response = auth_client(superadmin).delete(reverse('branches-detail', args=[branch.id]))

        assert response.status_code == 204
        assert not Branch.objects.filter(id=branch.id).exists()
        assert Branch.all_objects.filter(id=branch.id, is_deleted=True).exists()

    def test_search_by_code(self, auth_client, operator):
        BranchFactory(name='Ош Южный', code='OSH')
        BranchFactory(name='Бишкек', code='BSH')

        response = auth_client(operator).get(BRANCHES_URL, {'search': 'OSH'})
        body = response.json()

        assert body['meta']['total'] == 1
        assert body['data'][0]['code'] == 'OSH'
