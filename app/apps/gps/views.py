from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import ActionPermissionsMixin, RolePermission
from apps.gps.models import Geofence
from apps.gps.serializers import (
    GeofenceSerializer,
    GPSEventSerializer,
    GPSLogSerializer,
    GPSUpdateSerializer,
    LivePointSerializer,
)
from apps.gps.services import GPSSelector, GPSService
from apps.users.choices import Roles


class CanUpdateGPS(RolePermission):
    allowed_roles = (Roles.DRIVER,)


class CanViewGPS(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.WAREHOUSE)


class CanManageGeofences(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR)


@extend_schema(tags=['gps'])
class GPSUpdateView(APIView):
    """Водитель отправляет координаты (ТЗ, разделы 03, 10). Лимит 1/5 сек."""

    permission_classes = (CanUpdateGPS,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'gps'

    @extend_schema(
        request=GPSUpdateSerializer, responses=GPSLogSerializer, summary='Отправка координат водителем'
    )
    def post(self, request):
        serializer = GPSUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        log = GPSService.update(
            driver=request.user,
            latitude=data['lat'],
            longitude=data['lng'],
            speed=data['speed'],
            heading=data['heading'],
            altitude=data['altitude'],
            accuracy=data['accuracy'],
            battery_level=data['battery_level'],
            device_time=data['device_time'],
            device_id=data['device_id'],
            app_version=data['app_version'],
        )
        return Response(GPSLogSerializer(log).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['gps'])
class GPSLiveView(APIView):
    """Онлайн-карта: последние точки машин в активных рейсах (ТЗ, раздел 10)."""

    permission_classes = (CanViewGPS,)

    @extend_schema(responses=LivePointSerializer(many=True), summary='Онлайн-точки автомобилей')
    def get(self, request):
        return Response(LivePointSerializer(GPSSelector.live(), many=True).data)


@extend_schema(tags=['gps'])
class GPSHistoryView(APIView):
    permission_classes = (CanViewGPS,)

    @extend_schema(responses=GPSLogSerializer(many=True), summary='История движения')
    def get(self, request):
        from apps.common.pagination import DefaultPageNumberPagination

        queryset = GPSSelector.history(
            vehicle_id=request.query_params.get('vehicle'),
            shipment_id=request.query_params.get('shipment'),
            date_from=request.query_params.get('date_from'),
            date_to=request.query_params.get('date_to'),
        )
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(GPSLogSerializer(page, many=True).data)


@extend_schema(tags=['gps'])
class GPSEventListView(APIView):
    permission_classes = (CanViewGPS,)

    @extend_schema(responses=GPSEventSerializer(many=True), summary='GPS-события')
    def get(self, request):
        from apps.common.pagination import DefaultPageNumberPagination
        from apps.gps.models import GPSEvent

        queryset = GPSEvent.objects.all()
        if request.query_params.get('vehicle'):
            queryset = queryset.filter(vehicle_id=request.query_params['vehicle'])
        if request.query_params.get('type'):
            queryset = queryset.filter(type=request.query_params['type'])
        paginator = DefaultPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        return paginator.get_paginated_response(GPSEventSerializer(page, many=True).data)


@extend_schema(tags=['gps'])
class GeofenceViewSet(ActionPermissionsMixin, ModelViewSet):
    serializer_class = GeofenceSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_fields = ('type', 'is_active')
    search_fields = ('name',)

    permission_classes_by_action = {
        '__default__': (CanViewGPS,),
        'create': (CanManageGeofences,),
        'partial_update': (CanManageGeofences,),
        'destroy': (CanManageGeofences,),
    }

    def get_queryset(self):
        return Geofence.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        instance.delete()
