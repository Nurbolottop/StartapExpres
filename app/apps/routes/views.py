from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import ActionPermissionsMixin, RolePermission
from apps.routes.models import Route, RoutePoint
from apps.routes.serializers import RoutePointSerializer, RouteSerializer
from apps.routes.services import RoutePointService, RouteService
from apps.users.choices import Roles


class CanManageRoutes(RolePermission):
    """Изменение маршрутов — Operator/Director/SuperAdmin (ТЗ, раздел 09)."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)


class _CrudViewSet(ActionPermissionsMixin, ModelViewSet):
    service: type
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    permission_classes_by_action = {
        '__default__': (IsAuthenticated,),
        'create': (CanManageRoutes,),
        'partial_update': (CanManageRoutes,),
        'destroy': (CanManageRoutes,),
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


@extend_schema(tags=['routes'])
class RouteViewSet(_CrudViewSet):
    serializer_class = RouteSerializer
    service = RouteService
    filterset_fields = ('start_branch', 'end_branch', 'is_active')
    search_fields = ('name', 'code')
    ordering_fields = ('name', 'created_at')

    def get_queryset(self):
        return Route.objects.select_related('start_branch', 'end_branch').prefetch_related('points')


@extend_schema(tags=['routes'])
class RoutePointViewSet(_CrudViewSet):
    serializer_class = RoutePointSerializer
    service = RoutePointService
    filterset_fields = ('route', 'city')
    ordering_fields = ('sequence',)

    def get_queryset(self):
        return RoutePoint.objects.select_related('route', 'city')
