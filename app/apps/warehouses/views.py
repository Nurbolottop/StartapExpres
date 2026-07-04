from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import ActionPermissionsMixin
from apps.warehouses.permissions import (
    CanManageWarehouses,
    CanManageWarehouseStructure,
    CanViewWarehouses,
)
from apps.warehouses.selectors import WarehouseSelector
from apps.warehouses.serializers import (
    WarehouseCellSerializer,
    WarehouseSerializer,
    WarehouseZoneSerializer,
)
from apps.warehouses.services import CellService, WarehouseService, ZoneService


class _CrudViewSet(ActionPermissionsMixin, ModelViewSet):
    service: type
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.service.create(actor=request.user, data=serializer.validated_data)
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = self.service.update(
            actor=request.user, instance=self.get_object(), data=serializer.validated_data
        )
        return Response(self.get_serializer(instance).data)

    def destroy(self, request, *args, **kwargs):
        self.service.soft_delete(actor=request.user, instance=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['warehouses'])
class WarehouseViewSet(_CrudViewSet):
    serializer_class = WarehouseSerializer
    service = WarehouseService
    filterset_fields = ('branch', 'is_active')
    search_fields = ('name', 'code', 'address')
    ordering_fields = ('name', 'created_at')

    permission_classes_by_action = {
        '__default__': (CanViewWarehouses,),
        'create': (CanManageWarehouses,),
        'partial_update': (CanManageWarehouses,),
        'destroy': (CanManageWarehouses,),
    }

    def get_queryset(self):
        return WarehouseSelector.list()


@extend_schema(tags=['warehouses'])
class WarehouseZoneViewSet(_CrudViewSet):
    serializer_class = WarehouseZoneSerializer
    service = ZoneService
    filterset_fields = ('warehouse', 'type', 'is_active')
    search_fields = ('name', 'code')
    ordering_fields = ('code', 'created_at')

    permission_classes_by_action = {
        '__default__': (CanViewWarehouses,),
        'create': (CanManageWarehouseStructure,),
        'partial_update': (CanManageWarehouseStructure,),
        'destroy': (CanManageWarehouseStructure,),
    }

    def get_queryset(self):
        return WarehouseSelector.zones()


@extend_schema(tags=['warehouses'])
class WarehouseCellViewSet(_CrudViewSet):
    serializer_class = WarehouseCellSerializer
    service = CellService
    filterset_fields = ('zone', 'is_active')
    search_fields = ('code', 'shelf', 'row')
    ordering_fields = ('code', 'created_at')

    permission_classes_by_action = {
        '__default__': (CanViewWarehouses,),
        'create': (CanManageWarehouseStructure,),
        'partial_update': (CanManageWarehouseStructure,),
        'destroy': (CanManageWarehouseStructure,),
        'available': (CanViewWarehouses,),
    }

    def get_queryset(self):
        return WarehouseSelector.cells()

    @extend_schema(responses=WarehouseCellSerializer(many=True), summary='Ячейки со свободной вместимостью')
    @action(detail=False, methods=['get'])
    def available(self, request):
        queryset = self.filter_queryset(WarehouseSelector.available_cells())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
