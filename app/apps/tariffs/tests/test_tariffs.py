from decimal import Decimal

import pytest
from django.urls import reverse

from apps.branches.tests.factories import CityFactory
from apps.tariffs.exceptions import TariffNotFoundException
from apps.tariffs.services import TariffService
from apps.tariffs.tests.factories import AdditionalServiceFactory, TariffFactory

pytestmark = pytest.mark.django_db

TARIFFS_URL = reverse('tariffs-list')
CALCULATE_URL = reverse('tariffs-calculate')


class TestTariffCrud:
    def test_director_creates_tariff(self, auth_client, director):
        response = auth_client(director).post(
            TARIFFS_URL,
            {
                'name': 'Базовый',
                'code': 'BASE',
                'base_price': '200',
                'price_per_kg': '50',
                'min_price': '300',
            },
        )

        assert response.status_code == 201

    def test_operator_cannot_create_tariff(self, auth_client, operator):
        response = auth_client(operator).post(TARIFFS_URL, {'name': 'X', 'code': 'X', 'base_price': '1'})

        assert response.status_code == 403


class TestCalculation:
    def test_full_formula(self, auth_client, client_user):
        bishkek, osh = CityFactory(), CityFactory()
        TariffFactory(
            from_city=bishkek,
            to_city=osh,
            base_price=200,
            price_per_kg=50,
            price_per_m3=1000,
            insurance_percent=1,
        )
        packing = AdditionalServiceFactory(price=150)

        response = auth_client(client_user).post(
            CALCULATE_URL,
            {
                'from_city': str(bishkek.id),
                'to_city': str(osh.id),
                'weight': '10',
                'volume': '0.5',
                'declared_value': '5000',
                'services': [str(packing.id)],
            },
        )
        body = response.json()

        assert response.status_code == 200
        # 200 + 10*50 + 0.5*1000 + 150 + 5000*1% = 200+500+500+150+50 = 1400
        assert body['data']['total_price'] == '1400.00'
        assert body['data']['insurance_price'] == '50.00'

    def test_min_price_applied(self, client_user):
        bishkek, osh = CityFactory(), CityFactory()
        TariffFactory(
            from_city=bishkek, to_city=osh, base_price=100, price_per_kg=0, price_per_m3=0, min_price=500
        )

        result = TariffService.calculate(
            from_city=bishkek, to_city=osh, weight=Decimal('1'), volume=Decimal('0')
        )

        assert result['total_price'] == Decimal('500.00')

    def test_fallback_to_default_tariff(self, client_user):
        default = TariffFactory(from_city=None, to_city=None, base_price=999, price_per_kg=0, price_per_m3=0)
        a, b = CityFactory(), CityFactory()

        result = TariffService.calculate(from_city=a, to_city=b, weight=Decimal('1'), volume=Decimal('0'))

        assert result['tariff'] == default
        assert result['total_price'] == Decimal('999.00')

    def test_exact_route_beats_default(self, client_user):
        TariffFactory(from_city=None, to_city=None, base_price=999)
        a, b = CityFactory(), CityFactory()
        exact = TariffFactory(from_city=a, to_city=b, base_price=100, price_per_kg=0, price_per_m3=0)

        result = TariffService.calculate(from_city=a, to_city=b, weight=Decimal('0'), volume=Decimal('0'))

        assert result['tariff'] == exact

    def test_no_tariff_raises_business_error(self, auth_client, client_user):
        a, b = CityFactory(), CityFactory()

        response = auth_client(client_user).post(
            CALCULATE_URL, {'from_city': str(a.id), 'to_city': str(b.id), 'weight': '1'}
        )

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'TARIFF_001'

    def test_service_raises_without_default(self):
        a, b = CityFactory(), CityFactory()

        with pytest.raises(TariffNotFoundException):
            TariffService.find_for_route(a, b)
