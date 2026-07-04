from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.branches.tests.factories import BranchFactory, CityFactory
from apps.gps.choices import GPSEventType
from apps.gps.models import Geofence, GPSEvent, GPSLog
from apps.gps.services import GPSService
from apps.gps.tasks import check_offline_vehicles, detect_long_stops
from apps.routes.models import Route
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment
from apps.shipments.services import ShipmentService
from apps.vehicles.tests.factories import VehicleFactory

pytestmark = pytest.mark.django_db

UPDATE_URL = reverse('gps-update')
LIVE_URL = reverse('gps-live')


@pytest.fixture
def active_shipment(superadmin, driver):
    start_city = CityFactory(latitude='42.87', longitude='74.59')
    end_city = CityFactory(latitude='40.51', longitude='72.80')
    start = BranchFactory(city=start_city)
    end = BranchFactory(city=end_city)
    route = Route.objects.create(
        name='Т',
        code='TT',
        start_branch=start,
        end_branch=end,
        estimated_distance=600,
        estimated_duration=600,
    )
    shipment = ShipmentService.create(
        actor=superadmin,
        departure_branch=start,
        arrival_branch=end,
        route=route,
        vehicle=VehicleFactory(),
        driver=driver,
    )
    Shipment.objects.filter(id=shipment.id).update(status=ShipmentStatus.IN_TRANSIT)
    shipment.refresh_from_db()
    return shipment


def gps_payload(**extra) -> dict:
    payload = {'lat': '42.5', 'lng': '74.0', 'speed': '60', 'device_time': timezone.now().isoformat()}
    payload.update(extra)
    return payload


class TestGPSUpdate:
    def test_driver_sends_point_and_live_updates(self, auth_client, driver, operator, active_shipment):
        response = auth_client(driver).post(UPDATE_URL, gps_payload())

        assert response.status_code == 201
        assert GPSLog.objects.filter(shipment=active_shipment).count() == 1

        live = auth_client(operator).get(LIVE_URL).json()
        assert len(live['data']) == 1
        assert live['data'][0]['shipment_number'] == active_shipment.shipment_number
        assert live['data'][0]['eta_minutes'] is not None

    def test_non_driver_cannot_send(self, auth_client, operator):
        response = auth_client(operator).post(UPDATE_URL, gps_payload())

        assert response.status_code == 403

    def test_bad_accuracy_rejected(self, auth_client, driver, active_shipment):
        response = auth_client(driver).post(UPDATE_URL, gps_payload(accuracy='150'))

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'GPS_002'

    def test_stale_point_rejected(self, auth_client, driver, active_shipment):
        stale = (timezone.now() - timedelta(minutes=10)).isoformat()

        response = auth_client(driver).post(UPDATE_URL, gps_payload(device_time=stale))

        assert response.status_code == 422

    def test_driver_without_active_shipment_rejected(self, auth_client, driver):
        response = auth_client(driver).post(UPDATE_URL, gps_payload())

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'GPS_006'

    def test_overspeed_creates_event(self, driver, active_shipment):
        GPSService.update(
            driver=driver,
            latitude=Decimal('42.5'),
            longitude=Decimal('74.0'),
            device_time=timezone.now(),
            speed=Decimal('120'),
        )

        event = GPSEvent.objects.filter(type=GPSEventType.OVERSPEED).first()
        assert event is not None
        assert event.shipment == active_shipment

    def test_geofence_enter_event(self, driver, active_shipment):
        Geofence.objects.create(name='Склад Бишкек', latitude='42.87', longitude='74.59', radius_m=1000)
        # первая точка вне зоны, вторая — внутри
        GPSService.update(
            driver=driver, latitude=Decimal('42.5'), longitude=Decimal('74.0'), device_time=timezone.now()
        )
        GPSService.update(
            driver=driver,
            latitude=Decimal('42.8701'),
            longitude=Decimal('74.5901'),
            device_time=timezone.now(),
        )

        assert GPSEvent.objects.filter(type=GPSEventType.ENTER_GEOFENCE).exists()

    def test_history_endpoint(self, auth_client, driver, operator, active_shipment):
        auth_client(driver).post(UPDATE_URL, gps_payload())

        response = auth_client(operator).get(
            reverse('gps-history'), {'vehicle': str(active_shipment.vehicle_id)}
        )

        assert response.status_code == 200
        assert response.json()['meta']['total'] == 1

    def test_gps_log_immutable(self, driver, active_shipment):
        log = GPSService.update(
            driver=driver, latitude=Decimal('42.5'), longitude=Decimal('74.0'), device_time=timezone.now()
        )

        log.speed = Decimal('99')
        with pytest.raises(ValueError):
            log.save()


class TestGPSTasks:
    def test_offline_60_minutes_marks_shipment_gps_lost(self, active_shipment):
        Shipment.objects.filter(id=active_shipment.id).update(
            departure_time=timezone.now() - timedelta(minutes=90)
        )

        flagged = check_offline_vehicles()

        active_shipment.refresh_from_db()
        assert flagged == 1
        assert active_shipment.status == ShipmentStatus.GPS_LOST

    def test_offline_10_minutes_publishes_notification(self, active_shipment, driver):
        GPSService.update(
            driver=driver, latitude=Decimal('42.5'), longitude=Decimal('74.0'), device_time=timezone.now()
        )
        GPSLog.objects.filter(shipment=active_shipment).update(
            server_time=timezone.now() - timedelta(minutes=15)
        )

        flagged = check_offline_vehicles()

        active_shipment.refresh_from_db()
        assert flagged == 1
        assert active_shipment.status == ShipmentStatus.IN_TRANSIT  # ещё не потерян

    def test_long_stop_detected(self, active_shipment, driver):
        GPSService.update(
            driver=driver,
            latitude=Decimal('42.5'),
            longitude=Decimal('74.0'),
            device_time=timezone.now(),
            speed=Decimal('0'),
        )

        detected = detect_long_stops()

        assert detected == 1
        assert GPSEvent.objects.filter(type=GPSEventType.LONG_STOP, shipment=active_shipment).exists()

    def test_long_stop_not_detected_when_moving(self, active_shipment, driver):
        GPSService.update(
            driver=driver,
            latitude=Decimal('42.5'),
            longitude=Decimal('74.0'),
            device_time=timezone.now(),
            speed=Decimal('60'),
        )

        assert detect_long_stops() == 0
