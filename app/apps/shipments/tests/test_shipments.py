import pytest
from django.urls import reverse

from apps.branches.tests.factories import BranchFactory
from apps.orders.choices import OrderStatus
from apps.orders.tests.factories import OrderFactory
from apps.packages.choices import PackageStatus
from apps.packages.models import Package
from apps.packages.services import PackageService
from apps.routes.models import Route
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment
from apps.shipments.services import ShipmentService
from apps.users.choices import DriverStatus, Roles
from apps.users.tests.factories import UserFactory
from apps.vehicles.choices import VehicleStatus
from apps.vehicles.tests.factories import VehicleFactory

pytestmark = pytest.mark.django_db

SHIPMENTS_URL = reverse('shipments-list')


def shipment_url(shipment_id, suffix: str = '') -> str:
    base = reverse('shipments-detail', args=[shipment_id])
    return f'{base}{suffix}' if suffix else base


@pytest.fixture
def route_obj():
    return Route.objects.create(
        name='Бишкек — Ош',
        code='BSHOSH',
        start_branch=BranchFactory(),
        end_branch=BranchFactory(),
        estimated_distance=600,
        estimated_duration=600,
    )


def make_ready_order(superadmin, weight=10):
    """Заказ в статусе WAITING_SHIPMENT с QR-грузом."""
    order = OrderFactory(status=OrderStatus.WAITING_SHIPMENT)
    package = Package.objects.create(
        order=order, title='Коробка', weight=weight, volume=0.1, status=PackageStatus.STORED
    )
    package = PackageService.generate_qr(actor=superadmin, package=package)
    return order, package


def make_shipment(superadmin, driver, route_obj, vehicle=None) -> Shipment:
    vehicle = vehicle or VehicleFactory(max_weight=1000, max_volume=10)
    return ShipmentService.create(
        actor=superadmin,
        departure_branch=route_obj.start_branch,
        arrival_branch=route_obj.end_branch,
        route=route_obj,
        vehicle=vehicle,
        driver=driver,
    )


class TestShipmentCreation:
    def test_operator_creates_shipment(self, auth_client, operator, route_obj, driver):
        vehicle = VehicleFactory()
        payload = {
            'departure_branch': str(route_obj.start_branch.id),
            'arrival_branch': str(route_obj.end_branch.id),
            'route': str(route_obj.id),
            'vehicle': str(vehicle.id),
            'driver': str(driver.id),
        }

        response = auth_client(operator).post(SHIPMENTS_URL, payload, format='json')
        body = response.json()

        assert response.status_code == 201
        assert body['data']['shipment_number'].startswith('SHP-')
        assert body['data']['status'] == ShipmentStatus.DRAFT

    def test_driver_cannot_create_shipment(self, auth_client, driver, route_obj):
        response = auth_client(driver).post(SHIPMENTS_URL, {}, format='json')

        assert response.status_code == 403

    def test_vehicle_busy_in_other_active_shipment(self, superadmin, driver, route_obj):
        vehicle = VehicleFactory()
        first = make_shipment(superadmin, driver, route_obj, vehicle=vehicle)
        Shipment.objects.filter(id=first.id).update(status=ShipmentStatus.IN_TRANSIT)
        other_driver = UserFactory(role=Roles.DRIVER)

        from apps.shipments.exceptions import VehicleBusyException

        with pytest.raises(VehicleBusyException):
            ShipmentService.create(
                actor=superadmin,
                departure_branch=route_obj.start_branch,
                arrival_branch=route_obj.end_branch,
                vehicle=vehicle,
                driver=other_driver,
            )

    def test_driver_busy_in_other_active_shipment(self, superadmin, driver, route_obj):
        first = make_shipment(superadmin, driver, route_obj)
        Shipment.objects.filter(id=first.id).update(status=ShipmentStatus.IN_TRANSIT)

        from apps.shipments.exceptions import DriverBusyException

        with pytest.raises(DriverBusyException):
            make_shipment(superadmin, driver, route_obj)


class TestShipmentComposition:
    def test_add_order_requires_waiting_shipment_status(self, superadmin, driver, route_obj):
        shipment = make_shipment(superadmin, driver, route_obj)
        unpaid = OrderFactory(status=OrderStatus.WAITING_PAYMENT)

        from apps.shipments.exceptions import OrderNotReadyException

        with pytest.raises(OrderNotReadyException):
            ShipmentService.add_order(actor=superadmin, shipment=shipment, order=unpaid)

    def test_add_order_moves_packages_to_waiting_loading(self, superadmin, driver, route_obj):
        shipment = make_shipment(superadmin, driver, route_obj)
        order, package = make_ready_order(superadmin)

        ShipmentService.add_order(actor=superadmin, shipment=shipment, order=order)

        package.refresh_from_db()
        assert package.status == PackageStatus.WAITING_LOADING
        assert shipment.items.count() == 1

    def test_order_cannot_be_in_two_active_shipments(self, superadmin, driver, route_obj):
        shipment = make_shipment(superadmin, driver, route_obj)
        order, _ = make_ready_order(superadmin)
        ShipmentService.add_order(actor=superadmin, shipment=shipment, order=order)
        other = make_shipment(superadmin, UserFactory(role=Roles.DRIVER), route_obj)

        from apps.shipments.exceptions import OrderAlreadyInShipmentException

        with pytest.raises(OrderAlreadyInShipmentException):
            ShipmentService.add_order(actor=superadmin, shipment=other, order=order)

    def test_weight_limit_enforced(self, superadmin, driver, route_obj):
        vehicle = VehicleFactory(max_weight=15, max_volume=10)
        shipment = make_shipment(superadmin, driver, route_obj, vehicle=vehicle)
        order, _ = make_ready_order(superadmin, weight=20)

        from apps.shipments.exceptions import WeightLimitException

        with pytest.raises(WeightLimitException):
            ShipmentService.add_order(actor=superadmin, shipment=shipment, order=order)


class TestShipmentLifecycle:
    def _prepare_loaded(self, superadmin, warehouse_user, driver, route_obj):
        shipment = make_shipment(superadmin, driver, route_obj)
        order, package = make_ready_order(superadmin)
        ShipmentService.add_order(actor=superadmin, shipment=shipment, order=order)
        from apps.shipments.services import ShipmentTransitionService

        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.PLANNED, actor=superadmin
        )
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.READY, actor=superadmin
        )
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.LOADING, actor=warehouse_user
        )
        ShipmentService.load_package(actor=warehouse_user, shipment=shipment, qr_code=package.qr_code)
        return shipment, order, package

    def test_finish_loading_requires_all_scanned(self, superadmin, warehouse_user, driver, route_obj):
        shipment = make_shipment(superadmin, driver, route_obj)
        order, _ = make_ready_order(superadmin)
        ShipmentService.add_order(actor=superadmin, shipment=shipment, order=order)
        from apps.shipments.services import ShipmentTransitionService

        for target in (ShipmentStatus.PLANNED, ShipmentStatus.READY):
            shipment = ShipmentTransitionService.change(shipment=shipment, to_status=target, actor=superadmin)
        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.LOADING, actor=warehouse_user
        )

        from apps.shipments.exceptions import MissingPackageException

        with pytest.raises(MissingPackageException):
            ShipmentService.finish_loading(actor=warehouse_user, shipment=shipment)

    def test_full_trip_lifecycle(self, superadmin, warehouse_user, driver, route_obj):
        shipment, order, package = self._prepare_loaded(superadmin, warehouse_user, driver, route_obj)

        shipment = ShipmentService.finish_loading(actor=warehouse_user, shipment=shipment)
        order.refresh_from_db()
        assert shipment.status == ShipmentStatus.LOADED
        assert order.status == OrderStatus.LOADED

        shipment = ShipmentService.start(actor=driver, shipment=shipment)
        order.refresh_from_db()
        package.refresh_from_db()
        shipment.vehicle.refresh_from_db()
        driver.driver_profile.refresh_from_db()
        assert shipment.status == ShipmentStatus.IN_TRANSIT
        assert order.status == OrderStatus.IN_TRANSIT
        assert package.status == PackageStatus.IN_TRANSIT
        assert shipment.vehicle.status == VehicleStatus.BUSY
        assert driver.driver_profile.status == DriverStatus.ON_TRIP

        shipment = ShipmentService.arrive(actor=driver, shipment=shipment)
        order.refresh_from_db()
        assert order.status == OrderStatus.ARRIVED

        from apps.shipments.services import ShipmentTransitionService

        shipment = ShipmentTransitionService.change(
            shipment=shipment, to_status=ShipmentStatus.UNLOADING, actor=warehouse_user
        )
        ShipmentService.unload_package(actor=warehouse_user, shipment=shipment, qr_code=package.qr_code)
        shipment = ShipmentService.finish(actor=warehouse_user, shipment=shipment)

        order.refresh_from_db()
        package.refresh_from_db()
        shipment.vehicle.refresh_from_db()
        assert shipment.status == ShipmentStatus.COMPLETED
        assert order.status == OrderStatus.READY_FOR_PICKUP
        assert package.status == PackageStatus.READY_FOR_PICKUP
        assert shipment.vehicle.status == VehicleStatus.AVAILABLE

    def test_start_checklist_blocks_without_driver(self, superadmin, warehouse_user, route_obj, driver):
        shipment, _, _ = self._prepare_loaded(superadmin, warehouse_user, driver, route_obj)
        shipment = ShipmentService.finish_loading(actor=warehouse_user, shipment=shipment)
        Shipment.objects.filter(id=shipment.id).update(driver=None)
        shipment.refresh_from_db()

        from apps.shipments.exceptions import ShipmentChecklistException

        with pytest.raises(ShipmentChecklistException):
            ShipmentService.start(actor=superadmin, shipment=shipment)

    def test_foreign_driver_cannot_start(self, superadmin, warehouse_user, driver, route_obj):
        shipment, _, _ = self._prepare_loaded(superadmin, warehouse_user, driver, route_obj)
        shipment = ShipmentService.finish_loading(actor=warehouse_user, shipment=shipment)
        stranger = UserFactory(role=Roles.DRIVER)

        from apps.shipments.exceptions import ShipmentTransitionRoleException

        with pytest.raises(ShipmentTransitionRoleException):
            ShipmentService.start(actor=stranger, shipment=shipment)

    def test_cancel_after_start_forbidden(self, superadmin, warehouse_user, driver, route_obj):
        shipment, _, _ = self._prepare_loaded(superadmin, warehouse_user, driver, route_obj)
        shipment = ShipmentService.finish_loading(actor=warehouse_user, shipment=shipment)
        shipment = ShipmentService.start(actor=driver, shipment=shipment)

        from apps.shipments.exceptions import InvalidShipmentTransitionException

        with pytest.raises(InvalidShipmentTransitionException):
            ShipmentService.cancel(actor=superadmin, shipment=shipment)


class TestDriverScoping:
    def test_driver_sees_only_own_shipments(self, auth_client, superadmin, driver, route_obj):
        make_shipment(superadmin, driver, route_obj)
        make_shipment(superadmin, UserFactory(role=Roles.DRIVER), route_obj)

        response = auth_client(driver).get(SHIPMENTS_URL)

        assert response.json()['meta']['total'] == 1

    def test_driver_reports_incident(self, auth_client, superadmin, driver, route_obj):
        shipment = make_shipment(superadmin, driver, route_obj)

        response = auth_client(driver).post(
            shipment_url(shipment.id, 'incidents/'),
            {'type': 'breakdown', 'description': 'Пробито колесо', 'latitude': '42.1', 'longitude': '74.1'},
        )

        assert response.status_code == 201
        assert shipment.incidents.count() == 1


class TestRoutes:
    def test_operator_creates_route(self, auth_client, operator):
        start, end = BranchFactory(), BranchFactory()

        response = auth_client(operator).post(
            reverse('routes-list'),
            {
                'name': 'Бишкек — Каракол',
                'code': 'BSHKRK',
                'start_branch': str(start.id),
                'end_branch': str(end.id),
                'estimated_distance': '400',
                'estimated_duration': 420,
            },
        )

        assert response.status_code == 201

    def test_route_points_ordering_unique(self, auth_client, operator, route_obj):
        from apps.branches.tests.factories import CityFactory

        city = CityFactory()
        url = reverse('route-points-list')
        first = auth_client(operator).post(
            url, {'route': str(route_obj.id), 'city': str(city.id), 'sequence': 1}
        )
        duplicate = auth_client(operator).post(
            url, {'route': str(route_obj.id), 'city': str(city.id), 'sequence': 1}
        )

        assert first.status_code == 201
        assert duplicate.status_code == 400
