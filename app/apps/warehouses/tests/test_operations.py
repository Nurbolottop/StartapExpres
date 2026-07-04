import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.orders.choices import OrderStatus
from apps.orders.tests.factories import OrderFactory
from apps.packages.choices import PackageStatus, PhotoType
from apps.packages.models import Package, PackagePhoto
from apps.packages.services import PackageService
from apps.warehouses.models import DeliveryConfirmation, WarehouseMovement
from apps.warehouses.operations import DeliveryService, InventoryService
from apps.warehouses.tests.factories import CellFactory, WarehouseFactory, ZoneFactory

pytestmark = pytest.mark.django_db

PNG = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90'
    b'wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x9a\x92\xdd\xd0\x00\x00'
    b'\x00\x00IEND\xaeB`\x82'
)


def photo(package: Package, photo_type: str) -> PackagePhoto:
    return PackagePhoto.objects.create(
        package=package,
        image=SimpleUploadedFile('p.png', PNG, content_type='image/png'),
        type=photo_type,
    )


def make_package(status=PackageStatus.CREATED, with_qr=True, superadmin=None, **kwargs) -> Package:
    order = kwargs.pop('order', None) or OrderFactory(status=OrderStatus.WAITING_RECEIVE)
    package = Package.objects.create(order=order, title='Коробка', weight=10, volume=0.1, **kwargs)
    if with_qr and superadmin is not None:
        package = PackageService.generate_qr(actor=superadmin, package=package)
    if status != PackageStatus.CREATED:
        Package.objects.filter(id=package.id).update(status=status)
        package.refresh_from_db()
    return package


class TestReceiving:
    def test_receive_requires_photo(self, auth_client, warehouse_user, superadmin):
        package = make_package(superadmin=superadmin)

        response = auth_client(warehouse_user).post(reverse('wh-receive'), {'qr_code': package.qr_code})

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'WAREHOUSE_004'

    def test_receive_with_photo_moves_order(self, auth_client, warehouse_user, superadmin):
        package = make_package(superadmin=superadmin)
        photo(package, PhotoType.RECEIVING)

        response = auth_client(warehouse_user).post(reverse('wh-receive'), {'qr_code': package.qr_code})

        assert response.status_code == 200
        package.refresh_from_db()
        assert package.status == PackageStatus.RECEIVED
        package.order.refresh_from_db()
        assert package.order.status == OrderStatus.RECEIVED

    def test_check_records_measurements(self, auth_client, warehouse_user, superadmin):
        package = make_package(status=PackageStatus.RECEIVED, superadmin=superadmin)

        response = auth_client(warehouse_user).post(
            reverse('wh-check'),
            {'qr_code': package.qr_code, 'weight': '12.5', 'length': 50, 'width': 40, 'height': 30},
        )

        assert response.status_code == 200
        package.refresh_from_db()
        assert package.status == PackageStatus.CHECKED
        assert str(package.weight) == '12.500'
        assert str(package.volume) == '0.060'


class TestStorageAndMovement:
    def test_store_occupies_cell(self, auth_client, warehouse_user, superadmin):
        package = make_package(status=PackageStatus.CHECKED, superadmin=superadmin)
        cell = CellFactory(capacity_weight=100, capacity_volume=5)

        response = auth_client(warehouse_user).post(
            reverse('wh-store'), {'qr_code': package.qr_code, 'cell': str(cell.id)}
        )

        assert response.status_code == 200
        cell.refresh_from_db()
        package.refresh_from_db()
        assert package.current_cell == cell
        assert package.status == PackageStatus.STORED
        assert cell.occupied_weight == 10
        assert WarehouseMovement.objects.filter(package=package, to_cell=cell).exists()

    def test_store_rejects_overflow(self, auth_client, warehouse_user, superadmin):
        package = make_package(status=PackageStatus.CHECKED, superadmin=superadmin)
        cell = CellFactory(capacity_weight=5, capacity_volume=5)

        response = auth_client(warehouse_user).post(
            reverse('wh-store'), {'qr_code': package.qr_code, 'cell': str(cell.id)}
        )

        assert response.status_code == 422
        assert response.json()['error']['code'] == 'WAREHOUSE_002'

    def test_store_without_qr_rejected(self, auth_client, warehouse_user):
        make_package(with_qr=False, status=PackageStatus.CHECKED)
        cell = CellFactory()
        # сканирование невозможно без QR — эмулируем прямой вызов по коду
        response = auth_client(warehouse_user).post(
            reverse('wh-store'), {'qr_code': 'missing-qr', 'cell': str(cell.id)}
        )

        assert response.status_code == 404

    def test_move_between_cells(self, auth_client, warehouse_user, superadmin):
        package = make_package(status=PackageStatus.CHECKED, superadmin=superadmin)
        first = CellFactory(capacity_weight=100, capacity_volume=5)
        second = CellFactory(capacity_weight=100, capacity_volume=5)
        client = auth_client(warehouse_user)
        client.post(reverse('wh-store'), {'qr_code': package.qr_code, 'cell': str(first.id)})

        response = client.post(
            reverse('wh-move'),
            {'qr_code': package.qr_code, 'to_cell': str(second.id), 'reason': 'уплотнение'},
        )

        assert response.status_code == 200
        first.refresh_from_db()
        second.refresh_from_db()
        assert first.occupied_weight == 0
        assert second.occupied_weight == 10
        assert WarehouseMovement.objects.filter(package=package).count() == 2

    def test_operator_cannot_operate_warehouse(self, auth_client, operator):
        response = auth_client(operator).post(reverse('wh-receive'), {'qr_code': 'x'})

        assert response.status_code == 403


class TestDamageAndLost:
    def test_damage_requires_photo_and_cascades(self, auth_client, warehouse_user, superadmin):
        order = OrderFactory(status=OrderStatus.IN_WAREHOUSE)
        package = make_package(order=order, status=PackageStatus.STORED, superadmin=superadmin)
        client = auth_client(warehouse_user)

        without_photo = client.post(
            reverse('wh-damage'), {'qr_code': package.qr_code, 'description': 'вмятина'}
        )
        photo(package, PhotoType.DAMAGE)
        with_photo = client.post(reverse('wh-damage'), {'qr_code': package.qr_code, 'description': 'вмятина'})

        assert without_photo.status_code == 422
        assert with_photo.status_code == 201
        package.refresh_from_db()
        order.refresh_from_db()
        assert package.status == PackageStatus.DAMAGED
        assert order.status == OrderStatus.DAMAGED

    def test_lost_report(self, auth_client, warehouse_user, superadmin):
        order = OrderFactory(status=OrderStatus.IN_WAREHOUSE)
        package = make_package(order=order, status=PackageStatus.STORED, superadmin=superadmin)

        response = auth_client(warehouse_user).post(
            reverse('wh-lost'), {'qr_code': package.qr_code, 'description': 'не найден'}
        )

        assert response.status_code == 201
        package.refresh_from_db()
        assert package.status == PackageStatus.LOST


class TestInventory:
    def test_inventory_finds_missing(self, warehouse_user, superadmin):
        warehouse = WarehouseFactory()
        zone = ZoneFactory(warehouse=warehouse)
        cell = CellFactory(zone=zone, capacity_weight=1000, capacity_volume=50)
        scanned_pkg = make_package(status=PackageStatus.STORED, superadmin=superadmin)
        missing_pkg = make_package(status=PackageStatus.STORED, superadmin=superadmin)
        Package.objects.filter(id__in=[scanned_pkg.id, missing_pkg.id]).update(current_cell=cell)

        session = InventoryService.open(actor=warehouse_user, warehouse=warehouse)
        InventoryService.scan(actor=warehouse_user, session=session, qr_code=scanned_pkg.qr_code)
        session = InventoryService.close(actor=warehouse_user, session=session)

        assert session.report['expected'] == 2
        assert session.report['scanned'] == 1
        assert session.report['missing_packages'] == [str(missing_pkg.id)]


class TestIssue:
    def test_issue_requires_scan_and_photo(self, auth_client, warehouse_user, superadmin):
        order = OrderFactory(status=OrderStatus.READY_FOR_PICKUP)
        package = make_package(order=order, status=PackageStatus.READY_FOR_PICKUP, superadmin=superadmin)
        url = reverse('order-issue', args=[order.id])
        client = auth_client(warehouse_user)
        payload = {'received_by_name': 'Болот', 'document_number': 'ID123', 'qr_codes': [package.qr_code]}

        without_photo = client.post(url, payload, format='json')
        photo(package, PhotoType.DELIVERY)
        missing_scan = client.post(url, {**payload, 'qr_codes': ['other']}, format='json')
        success = client.post(url, payload, format='json')

        assert without_photo.status_code == 422
        assert missing_scan.status_code == 422
        assert success.status_code == 201
        order.refresh_from_db()
        package.refresh_from_db()
        assert order.status == OrderStatus.DELIVERED
        assert package.status == PackageStatus.DELIVERED
        assert DeliveryConfirmation.objects.filter(order=order).exists()

    def test_issue_delivery_service_direct(self, warehouse_user, superadmin):
        order = OrderFactory(status=OrderStatus.READY_FOR_PICKUP)
        package = make_package(order=order, status=PackageStatus.READY_FOR_PICKUP, superadmin=superadmin)
        photo(package, PhotoType.DELIVERY)

        confirmation = DeliveryService.issue(
            actor=warehouse_user,
            order=order,
            received_by_name='Болот',
            document_number='AN123',
            qr_codes=[package.qr_code],
        )

        assert confirmation.received_by_name == 'Болот'
