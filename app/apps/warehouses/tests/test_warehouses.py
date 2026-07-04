import pytest
from django.urls import reverse

from apps.warehouses.exceptions import (
    CellNotEmptyException,
    WarehouseNotEmptyException,
    ZoneNotEmptyException,
)
from apps.warehouses.models import Warehouse
from apps.warehouses.services import CellService, WarehouseService, ZoneService
from apps.warehouses.tests.factories import CellFactory, WarehouseFactory, ZoneFactory

pytestmark = pytest.mark.django_db

WAREHOUSES_URL = reverse('warehouses-list')
ZONES_URL = reverse('warehouse-zones-list')
CELLS_URL = reverse('warehouse-cells-list')


class TestWarehouseCrud:
    def test_director_creates_warehouse(self, auth_client, director):
        from apps.branches.tests.factories import BranchFactory

        branch = BranchFactory()

        response = auth_client(director).post(
            WAREHOUSES_URL, {'branch': str(branch.id), 'name': 'Главный склад', 'code': 'WHMAIN'}
        )

        assert response.status_code == 201
        assert Warehouse.objects.filter(code='WHMAIN').exists()

    def test_warehouse_staff_creates_zone_and_cell(self, auth_client, warehouse_user):
        warehouse = WarehouseFactory()
        client = auth_client(warehouse_user)

        zone_response = client.post(
            ZONES_URL, {'warehouse': str(warehouse.id), 'name': 'Хранение', 'code': 'A1', 'type': 'storage'}
        )
        zone_id = zone_response.json()['data']['id']
        cell_response = client.post(
            CELLS_URL,
            {
                'zone': zone_id,
                'code': 'B14',
                'shelf': 'B',
                'row': '1',
                'level': '4',
                'capacity_weight': '500',
                'capacity_volume': '5',
            },
        )

        assert zone_response.status_code == 201
        assert cell_response.status_code == 201

    def test_operator_cannot_create_zone(self, auth_client, operator):
        warehouse = WarehouseFactory()

        response = auth_client(operator).post(
            ZONES_URL, {'warehouse': str(warehouse.id), 'name': 'X', 'code': 'X1'}
        )

        assert response.status_code == 403

    def test_duplicate_zone_code_in_warehouse_rejected(self, auth_client, superadmin):
        zone = ZoneFactory(code='A1')

        response = auth_client(superadmin).post(
            ZONES_URL, {'warehouse': str(zone.warehouse.id), 'name': 'Дубль', 'code': 'A1'}
        )

        assert response.status_code == 400


class TestDeletionRules:
    def test_cannot_delete_warehouse_with_zones(self, superadmin):
        zone = ZoneFactory()

        with pytest.raises(WarehouseNotEmptyException):
            WarehouseService.soft_delete(actor=superadmin, instance=zone.warehouse)

    def test_cannot_delete_zone_with_cells(self, superadmin):
        cell = CellFactory()

        with pytest.raises(ZoneNotEmptyException):
            ZoneService.soft_delete(actor=superadmin, instance=cell.zone)

    def test_cannot_delete_occupied_cell(self, superadmin):
        cell = CellFactory(occupied_weight=10)

        with pytest.raises(CellNotEmptyException):
            CellService.soft_delete(actor=superadmin, instance=cell)

    def test_empty_cell_deletes(self, auth_client, superadmin):
        cell = CellFactory()

        response = auth_client(superadmin).delete(reverse('warehouse-cells-detail', args=[cell.id]))

        assert response.status_code == 204


class TestAvailableCells:
    def test_available_excludes_full_cells(self, auth_client, warehouse_user):
        CellFactory(capacity_weight=100, occupied_weight=100)
        free = CellFactory(capacity_weight=100, occupied_weight=10)

        response = auth_client(warehouse_user).get(reverse('warehouse-cells-available'))
        body = response.json()

        assert response.status_code == 200
        assert body['meta']['total'] == 1
        assert body['data'][0]['id'] == str(free.id)
        assert body['data'][0]['free_weight'] == '90.00'
