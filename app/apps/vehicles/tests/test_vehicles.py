import pytest
from django.urls import reverse

from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle
from apps.vehicles.services import VehicleService
from apps.vehicles.tests.factories import VehicleFactory, VehicleTypeFactory

pytestmark = pytest.mark.django_db

VEHICLES_URL = reverse('vehicles-list')
TYPES_URL = reverse('vehicle-types-list')


def assign_url(vehicle_id) -> str:
    return reverse('vehicles-assign-driver', args=[vehicle_id])


class TestVehicleCrud:
    def test_director_creates_vehicle(self, auth_client, director):
        vehicle_type = VehicleTypeFactory()
        payload = {
            'vehicle_type': str(vehicle_type.id),
            'plate_number': '01KG777ABC',
            'brand': 'Isuzu',
            'max_weight': '5000',
            'max_volume': '30',
        }

        response = auth_client(director).post(VEHICLES_URL, payload)

        assert response.status_code == 201
        assert Vehicle.objects.filter(plate_number='01KG777ABC').exists()

    def test_operator_cannot_create_vehicle(self, auth_client, operator):
        response = auth_client(operator).post(VEHICLES_URL, {'plate_number': 'X'})

        assert response.status_code == 403

    def test_driver_can_view_vehicles(self, auth_client, driver):
        VehicleFactory()

        response = auth_client(driver).get(VEHICLES_URL)

        assert response.status_code == 200
        assert response.json()['meta']['total'] == 1

    def test_superadmin_creates_vehicle_type(self, auth_client, superadmin):
        response = auth_client(superadmin).post(
            TYPES_URL, {'name': 'Рефрижератор', 'code': 'REF', 'max_weight': '10000', 'max_volume': '45'}
        )

        assert response.status_code == 201


class TestDriverAssignment:
    def test_operator_assigns_driver(self, auth_client, operator, driver):
        vehicle = VehicleFactory()

        response = auth_client(operator).post(assign_url(vehicle.id), {'driver': str(driver.id)})
        body = response.json()

        assert response.status_code == 200
        assert body['data']['driver_phone'] == driver.phone
        driver.refresh_from_db()
        assert driver.driver_profile.assigned_vehicle_id == vehicle.id

    def test_cannot_assign_non_driver(self, auth_client, operator, warehouse_user):
        vehicle = VehicleFactory()

        response = auth_client(operator).post(assign_url(vehicle.id), {'driver': str(warehouse_user.id)})

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'SHIPMENT_003'

    def test_cannot_assign_to_maintenance_vehicle(self, auth_client, operator, driver):
        vehicle = VehicleFactory(status=VehicleStatus.MAINTENANCE)

        response = auth_client(operator).post(assign_url(vehicle.id), {'driver': str(driver.id)})

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'SHIPMENT_002'

    def test_reassign_moves_driver_from_free_vehicle(self, superadmin, driver):
        first = VehicleFactory()
        second = VehicleFactory()
        VehicleService.assign_driver(actor=superadmin, vehicle=first, driver=driver)

        VehicleService.assign_driver(actor=superadmin, vehicle=second, driver=driver)

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.current_driver is None
        assert second.current_driver == driver

    def test_cannot_take_driver_from_busy_vehicle(self, superadmin, driver):
        busy = VehicleFactory()
        VehicleService.assign_driver(actor=superadmin, vehicle=busy, driver=driver)
        Vehicle.objects.filter(id=busy.id).update(status=VehicleStatus.BUSY)
        other = VehicleFactory()

        from apps.vehicles.exceptions import DriverUnavailableException

        with pytest.raises(DriverUnavailableException):
            VehicleService.assign_driver(actor=superadmin, vehicle=other, driver=driver)

    def test_unassign_driver(self, auth_client, operator, superadmin, driver):
        vehicle = VehicleFactory()
        VehicleService.assign_driver(actor=superadmin, vehicle=vehicle, driver=driver)

        response = auth_client(operator).post(reverse('vehicles-unassign-driver', args=[vehicle.id]))

        assert response.status_code == 200
        vehicle.refresh_from_db()
        assert vehicle.current_driver is None
        driver.refresh_from_db()
        assert driver.driver_profile.assigned_vehicle is None
