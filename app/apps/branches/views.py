from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.branches.permissions import CanManageBranches
from apps.branches.selectors import BranchSelector, CitySelector
from apps.branches.serializers import BranchSerializer, CitySerializer
from apps.branches.services import BranchService, CityService
from apps.common.permissions import ActionPermissionsMixin


class _ReferenceViewSet(ActionPermissionsMixin, ModelViewSet):
    """Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin."""

    service: type
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    permission_classes_by_action = {
        '__default__': (IsAuthenticated,),
        'create': (CanManageBranches,),
        'partial_update': (CanManageBranches,),
        'destroy': (CanManageBranches,),
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


@extend_schema(tags=['cities'])
class CityViewSet(_ReferenceViewSet):
    serializer_class = CitySerializer
    service = CityService
    filterset_fields = ('country', 'is_active')
    search_fields = ('name', 'code')
    ordering_fields = ('name', 'created_at')

    def get_queryset(self):
        return CitySelector.list()


@extend_schema(tags=['branches'])
class BranchViewSet(_ReferenceViewSet):
    serializer_class = BranchSerializer
    service = BranchService
    filterset_fields = ('city', 'is_main', 'is_active')
    search_fields = ('name', 'code', 'address', 'city__name')
    ordering_fields = ('name', 'created_at')

    def get_queryset(self):
        return BranchSelector.list()
