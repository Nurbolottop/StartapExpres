import uuid
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.branches.tests.factories import BranchFactory, CityFactory
from apps.notifications.models import Notification
from apps.routes.models import Route, RoutePoint
from apps.shipments.choices import ShipmentStatus
from apps.shipments.models import Shipment, ShipmentCheckpoint
from apps.shipments.services import ShipmentService
from apps.shipments.tests.test_shipments import make_ready_order, make_shipment
from apps.tracking.models import TrackingEvent
from apps.users.choices import Roles
from apps.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def checkpoints_url(shipment_id) -> str:
    return reverse('shipments-detail', args=[shipment_id]) + 'checkpoints/'


def payload(route_point, **overrides) -> dict:
    data = {
        'client_id': str(uuid.uuid4()),
        'route_point': str(route_point.id),
        'reached_at': timezone.now().isoformat(),
        'comment': 'перевал пройден',
    }
    data.update(overrides)
    return data


def make_route(code='BIS-OSH', cities=('Бишкек', 'Токтогул', 'Ош')) -> Route:
    route = Route.objects.create(
        name='Бишкек — Ош',
        code=code,
        start_branch=BranchFactory(),
        end_branch=BranchFactory(),
        estimated_distance=672,
        estimated_duration=720,
    )
    for sequence, name in enumerate(cities, start=1):
        RoutePoint.objects.create(route=route, city=CityFactory(name=name), sequence=sequence)
    return route


@pytest.fixture
def route():
    return make_route()


@pytest.fixture
def trip(superadmin, driver, route):
    """Рейс водителя с двумя заказами, переведённый в IN_TRANSIT."""
    shipment = make_shipment(superadmin, driver, route)
    orders = []
    for _ in range(2):
        order, _package = make_ready_order(superadmin)
        ShipmentService.add_order(actor=superadmin, shipment=shipment, order=order)
        orders.append(order)
    Shipment.objects.filter(id=shipment.id).update(status=ShipmentStatus.IN_TRANSIT)
    shipment.refresh_from_db()
    shipment.orders = orders
    return shipment


def toktogul(route) -> RoutePoint:
    return route.points.get(sequence=2)


def checkpoint_events():
    return TrackingEvent.objects.filter(status='checkpoint_reached')


def test_driver_marks_point_and_clients_see_tracking(auth_client, driver, trip, route):
    response = auth_client(driver).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')
    body = response.json()

    assert response.status_code == 201
    assert body['data']['city_name'] == 'Токтогул'
    assert body['data']['sequence'] == 2
    assert checkpoint_events().count() == 2
    for order in trip.orders:
        event = order.tracking_events.get(status='checkpoint_reached')
        assert event.comment == 'Токтогул'
        assert event.employee == driver


def test_clients_get_notifications(auth_client, driver, trip, route):
    auth_client(driver).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    notification = Notification.objects.filter(
        user=trip.orders[0].client, event_type='shipment.checkpoint_reached'
    ).first()
    assert notification is not None
    assert 'Токтогул' in notification.body


def test_same_client_id_is_idempotent(auth_client, driver, trip, route):
    data = payload(toktogul(route))
    client = auth_client(driver)

    first = client.post(checkpoints_url(trip.id), data, format='json')
    second = client.post(
        checkpoints_url(trip.id), data, format='json', HTTP_IDEMPOTENCY_KEY=data['client_id']
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()['data']['id'] == first.json()['data']['id']
    assert ShipmentCheckpoint.objects.count() == 1
    assert checkpoint_events().count() == 2


def test_same_point_twice_returns_existing(auth_client, driver, trip, route):
    client = auth_client(driver)
    first = client.post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    second = client.post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    assert second.status_code == 200
    assert second.json()['data']['id'] == first.json()['data']['id']
    assert ShipmentCheckpoint.objects.count() == 1
    assert checkpoint_events().count() == 2


def test_other_driver_forbidden(auth_client, trip, route):
    other = UserFactory(role=Roles.DRIVER)

    response = auth_client(other).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    # Чужой рейс водителю не виден вовсе (скоуп селектора)
    assert response.status_code in (403, 404)
    assert not ShipmentCheckpoint.objects.exists()


def test_other_driver_forbidden_in_service(superadmin, trip, route):
    from apps.shipments.exceptions import ShipmentTransitionRoleException
    from apps.shipments.services import ShipmentCheckpointService

    with pytest.raises(ShipmentTransitionRoleException):
        ShipmentCheckpointService.mark(
            actor=UserFactory(role=Roles.DRIVER),
            shipment=trip,
            client_id=uuid.uuid4(),
            route_point_id=toktogul(route).id,
            reached_at=timezone.now(),
        )


def test_client_role_forbidden(auth_client, client_user, trip, route):
    response = auth_client(client_user).post(
        checkpoints_url(trip.id), payload(toktogul(route)), format='json'
    )

    assert response.status_code in (403, 404)


def test_warehouse_can_read_but_not_write(auth_client, warehouse_user, driver, trip, route):
    auth_client(driver).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')
    client = auth_client(warehouse_user)

    read = client.get(checkpoints_url(trip.id))
    write = client.post(checkpoints_url(trip.id), payload(route.points.get(sequence=3)), format='json')

    assert read.status_code == 200
    assert [item['city_name'] for item in read.json()['data']] == ['Токтогул']
    assert write.status_code == 403


def test_operator_marks_for_driver(auth_client, operator, trip, route):
    response = auth_client(operator).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    assert response.status_code == 201


def test_point_from_other_route_rejected(auth_client, driver, trip):
    foreign = make_route(code='OSH-BIS').points.first()

    response = auth_client(driver).post(checkpoints_url(trip.id), payload(foreign), format='json')

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'SHIPMENT_011'


def test_before_start_rejected(auth_client, driver, trip, route):
    Shipment.objects.filter(id=trip.id).update(status=ShipmentStatus.LOADED)

    response = auth_client(driver).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'SHIPMENT_010'


def test_after_arrival_accepted(auth_client, driver, trip, route):
    Shipment.objects.filter(id=trip.id).update(status=ShipmentStatus.ARRIVED)

    response = auth_client(driver).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    assert response.status_code == 201


def test_shipment_without_route_rejected(auth_client, driver, trip, route):
    Shipment.objects.filter(id=trip.id).update(route=None)

    response = auth_client(driver).post(checkpoints_url(trip.id), payload(toktogul(route)), format='json')

    assert response.status_code == 422
    assert response.json()['error']['code'] == 'SHIPMENT_012'


def test_reached_at_in_future_rejected(auth_client, driver, trip, route):
    future = (timezone.now() + timedelta(hours=1)).isoformat()

    response = auth_client(driver).post(
        checkpoints_url(trip.id), payload(toktogul(route), reached_at=future), format='json'
    )

    assert response.status_code == 400
    assert response.json()['error']['code'] == 'VALIDATION_ERROR'


def test_list_sorted_by_reached_at(auth_client, driver, trip, route):
    client = auth_client(driver)
    now = timezone.now()
    client.post(
        checkpoints_url(trip.id),
        payload(route.points.get(sequence=3), reached_at=now.isoformat()),
        format='json',
    )
    client.post(
        checkpoints_url(trip.id),
        payload(route.points.get(sequence=1), reached_at=(now - timedelta(hours=2)).isoformat()),
        format='json',
    )

    response = client.get(checkpoints_url(trip.id))

    assert [item['sequence'] for item in response.json()['data']] == [1, 3]


def test_warehouse_sees_only_own_branch_shipments(auth_client, warehouse_user, trip):
    from apps.users.models import EmployeeProfile, User

    EmployeeProfile.objects.update_or_create(
        user=warehouse_user, defaults={'branch': trip.arrival_branch, 'employee_code': 'EMP-T1'}
    )
    other = make_shipment(trip.created_by, UserFactory(role=Roles.DRIVER), make_route(code='X-1'))

    response = auth_client(User.objects.get(id=warehouse_user.id)).get(reverse('shipments-list'))

    ids = {item['id'] for item in response.json()['data']}
    assert str(trip.id) in ids
    assert str(other.id) not in ids
