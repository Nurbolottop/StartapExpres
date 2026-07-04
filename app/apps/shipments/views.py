from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.idempotency import idempotent
from apps.common.permissions import ActionPermissionsMixin
from apps.shipments import permissions as shipment_permissions
from apps.shipments.choices import ShipmentStatus
from apps.shipments.selectors import ShipmentSelector
from apps.shipments.serializers import (
    AssignSerializer,
    IncidentCreateSerializer,
    IncidentSerializer,
    OrderRefSerializer,
    ShipmentCreateSerializer,
    ShipmentScanSerializer,
    ShipmentSerializer,
    ShipmentStatusHistorySerializer,
)
from apps.shipments.services import ShipmentService, ShipmentTransitionService


def _order(order_id):
    from apps.common.exceptions import NotFoundException
    from apps.orders.models import Order

    order = Order.objects.filter(id=order_id).first()
    if order is None:
        raise NotFoundException('Заказ не найден.')
    return order


@extend_schema(tags=['shipments'])
class ShipmentViewSet(ActionPermissionsMixin, ModelViewSet):
    """Рейсы (ТЗ, разделы 03, 09)."""

    serializer_class = ShipmentSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_fields = ('status', 'driver', 'vehicle', 'departure_branch', 'arrival_branch')
    search_fields = ('shipment_number', 'vehicle__plate_number', 'driver__phone')
    ordering_fields = ('created_at', 'planned_departure')

    permission_classes_by_action = {
        '__default__': (shipment_permissions.CanViewShipments,),
        'create': (shipment_permissions.CanCreateShipment,),
        'partial_update': (shipment_permissions.CanCreateShipment,),
        'destroy': (shipment_permissions.CanCreateShipment,),
        'assign_vehicle': (shipment_permissions.CanCreateShipment,),
        'assign_driver': (shipment_permissions.CanCreateShipment,),
        'add_order': (shipment_permissions.CanCreateShipment,),
        'remove_order': (shipment_permissions.CanCreateShipment,),
        'plan': (shipment_permissions.CanCreateShipment,),
        'ready': (shipment_permissions.CanCreateShipment,),
        'loading': (shipment_permissions.CanLoadShipment,),
        'load_package': (shipment_permissions.CanLoadShipment,),
        'loaded': (shipment_permissions.CanLoadShipment,),
        'start': (shipment_permissions.CanDriveShipment,),
        'arrive': (shipment_permissions.CanDriveShipment,),
        'unloading': (shipment_permissions.CanLoadShipment,),
        'unload_package': (shipment_permissions.CanLoadShipment,),
        'finish': (shipment_permissions.CanLoadShipment,),
        'incidents': (shipment_permissions.CanReportIncident,),
    }

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            from apps.shipments.models import Shipment

            return Shipment.objects.none()
        return ShipmentSelector.for_user(self.request.user)

    @extend_schema(
        request=ShipmentCreateSerializer, responses={201: ShipmentSerializer}, summary='Создать рейс'
    )
    @idempotent
    def create(self, request, *args, **kwargs):
        serializer = ShipmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = ShipmentService.create(actor=request.user, **serializer.validated_data)
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={204: None}, summary='Отменить рейс (до старта)')
    def destroy(self, request, *args, **kwargs):
        ShipmentService.cancel(actor=request.user, shipment=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=AssignSerializer, responses=ShipmentSerializer, summary='Назначить автомобиль')
    @action(detail=True, methods=['post'], url_path='assign-vehicle')
    def assign_vehicle(self, request, pk=None):
        from apps.common.exceptions import NotFoundException
        from apps.vehicles.models import Vehicle

        serializer = AssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vehicle = Vehicle.objects.filter(id=serializer.validated_data['id']).first()
        if vehicle is None:
            raise NotFoundException('Автомобиль не найден.')
        shipment = ShipmentService.assign_vehicle(
            actor=request.user, shipment=self.get_object(), vehicle=vehicle
        )
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=AssignSerializer, responses=ShipmentSerializer, summary='Назначить водителя')
    @action(detail=True, methods=['post'], url_path='assign-driver')
    def assign_driver(self, request, pk=None):
        from apps.common.exceptions import NotFoundException
        from apps.users.models import User

        serializer = AssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        driver = User.objects.filter(id=serializer.validated_data['id']).first()
        if driver is None:
            raise NotFoundException('Водитель не найден.')
        shipment = ShipmentService.assign_driver(
            actor=request.user, shipment=self.get_object(), driver=driver
        )
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=OrderRefSerializer, responses=ShipmentSerializer, summary='Добавить заказ в рейс')
    @action(detail=True, methods=['post'], url_path='add-order')
    def add_order(self, request, pk=None):
        serializer = OrderRefSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = ShipmentService.add_order(
            actor=request.user,
            shipment=self.get_object(),
            order=_order(serializer.validated_data['order']),
        )
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=OrderRefSerializer, responses=ShipmentSerializer, summary='Убрать заказ из рейса')
    @action(detail=True, methods=['post'], url_path='remove-order')
    def remove_order(self, request, pk=None):
        serializer = OrderRefSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shipment = ShipmentService.remove_order(
            actor=request.user,
            shipment=self.get_object(),
            order=_order(serializer.validated_data['order']),
        )
        return Response(ShipmentSerializer(shipment).data)

    def _transition(self, request, to_status: str):
        shipment = ShipmentTransitionService.change(
            shipment=self.get_object(), to_status=to_status, actor=request.user
        )
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Запланировать')
    @action(detail=True, methods=['post'])
    def plan(self, request, pk=None):
        return self._transition(request, ShipmentStatus.PLANNED)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Готов к погрузке')
    @action(detail=True, methods=['post'])
    def ready(self, request, pk=None):
        return self._transition(request, ShipmentStatus.READY)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Начать погрузку')
    @action(detail=True, methods=['post'])
    def loading(self, request, pk=None):
        return self._transition(request, ShipmentStatus.LOADING)

    @extend_schema(
        request=ShipmentScanSerializer, responses=ShipmentSerializer, summary='Скан груза при погрузке'
    )
    @action(detail=True, methods=['post'], url_path='load-package')
    def load_package(self, request, pk=None):
        serializer = ShipmentScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ShipmentService.load_package(
            actor=request.user, shipment=self.get_object(), **serializer.validated_data
        )
        return Response(ShipmentSerializer(self.get_object()).data)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Погрузка завершена')
    @action(detail=True, methods=['post'])
    def loaded(self, request, pk=None):
        shipment = ShipmentService.finish_loading(actor=request.user, shipment=self.get_object())
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Старт рейса (чек-лист)')
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        shipment = ShipmentService.start(actor=request.user, shipment=self.get_object())
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Прибытие')
    @action(detail=True, methods=['post'])
    def arrive(self, request, pk=None):
        shipment = ShipmentService.arrive(actor=request.user, shipment=self.get_object())
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Начать разгрузку')
    @action(detail=True, methods=['post'])
    def unloading(self, request, pk=None):
        return self._transition(request, ShipmentStatus.UNLOADING)

    @extend_schema(
        request=ShipmentScanSerializer, responses=ShipmentSerializer, summary='Скан груза при разгрузке'
    )
    @action(detail=True, methods=['post'], url_path='unload-package')
    def unload_package(self, request, pk=None):
        serializer = ShipmentScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ShipmentService.unload_package(
            actor=request.user, shipment=self.get_object(), **serializer.validated_data
        )
        return Response(ShipmentSerializer(self.get_object()).data)

    @extend_schema(request=None, responses=ShipmentSerializer, summary='Завершить рейс')
    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        shipment = ShipmentService.finish(actor=request.user, shipment=self.get_object())
        return Response(ShipmentSerializer(shipment).data)

    @extend_schema(
        request=IncidentCreateSerializer,
        responses={201: IncidentSerializer, 200: IncidentSerializer(many=True)},
        summary='Инциденты рейса (GET список, POST создать)',
    )
    @action(detail=True, methods=['get', 'post'])
    def incidents(self, request, pk=None):
        shipment = self.get_object()
        if request.method == 'GET':
            incidents = shipment.incidents.all()
            return Response(IncidentSerializer(incidents, many=True).data)
        serializer = IncidentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        incident = ShipmentService.report_incident(
            actor=request.user,
            shipment=shipment,
            incident_type=data['type'],
            description=data['description'],
            latitude=data['latitude'],
            longitude=data['longitude'],
        )
        return Response(IncidentSerializer(incident).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses=ShipmentStatusHistorySerializer(many=True), summary='История статусов')
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        history = self.get_object().status_history.select_related('changed_by').all()
        return Response(ShipmentStatusHistorySerializer(history, many=True).data)
