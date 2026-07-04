from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import ActionPermissionsMixin
from apps.vehicles.permissions import CanAssignDriver, CanManageVehicles, CanViewVehicles
from apps.vehicles.selectors import VehicleSelector, VehicleTypeSelector
from apps.vehicles.serializers import AssignDriverSerializer, VehicleSerializer, VehicleTypeSerializer
from apps.vehicles.services import VehicleService, VehicleTypeService


class _CrudViewSet(ActionPermissionsMixin, ModelViewSet):
    service: type
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    permission_classes_by_action = {
        '__default__': (CanViewVehicles,),
        'create': (CanManageVehicles,),
        'partial_update': (CanManageVehicles,),
        'destroy': (CanManageVehicles,),
    }

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


@extend_schema(tags=['vehicles'])
class VehicleTypeViewSet(_CrudViewSet):
    serializer_class = VehicleTypeSerializer
    service = VehicleTypeService
    filterset_fields = ('is_active',)
    search_fields = ('name', 'code')
    ordering_fields = ('name', 'created_at')

    def get_queryset(self):
        return VehicleTypeSelector.list()


@extend_schema(tags=['vehicles'])
class VehicleViewSet(_CrudViewSet):
    serializer_class = VehicleSerializer
    service = VehicleService
    filterset_fields = ('status', 'branch', 'vehicle_type', 'fuel_type', 'is_active')
    search_fields = ('plate_number', 'brand', 'model', 'vin')
    ordering_fields = ('plate_number', 'created_at', 'mileage')

    permission_classes_by_action = {
        **_CrudViewSet.permission_classes_by_action,
        'assign_driver': (CanAssignDriver,),
        'unassign_driver': (CanAssignDriver,),
    }

    def get_queryset(self):
        return VehicleSelector.list()

    @extend_schema(request=AssignDriverSerializer, responses=VehicleSerializer, summary='Назначить водителя')
    @action(detail=True, methods=['post'], url_path='assign-driver')
    def assign_driver(self, request, pk=None):
        serializer = AssignDriverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = VehicleService.assign_driver(
            actor=request.user,
            vehicle=self.get_object(),
            driver=serializer.validated_data['driver'],
        )
        return Response(VehicleSerializer(vehicle).data)

    @extend_schema(request=None, responses=VehicleSerializer, summary='Снять водителя')
    @action(detail=True, methods=['post'], url_path='unassign-driver')
    def unassign_driver(self, request, pk=None):
        vehicle = VehicleService.unassign_driver(actor=request.user, vehicle=self.get_object())
        return Response(VehicleSerializer(vehicle).data)
