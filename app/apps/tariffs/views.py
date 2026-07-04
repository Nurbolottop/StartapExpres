from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import ActionPermissionsMixin
from apps.tariffs.permissions import CanManageTariffs
from apps.tariffs.selectors import TariffSelector
from apps.tariffs.serializers import (
    AdditionalServiceSerializer,
    TariffCalculationRequestSerializer,
    TariffCalculationResponseSerializer,
    TariffSerializer,
)
from apps.tariffs.services import AdditionalServiceService, TariffService


class _CrudViewSet(ActionPermissionsMixin, ModelViewSet):
    service: type
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    permission_classes_by_action = {
        '__default__': (IsAuthenticated,),
        'create': (CanManageTariffs,),
        'partial_update': (CanManageTariffs,),
        'destroy': (CanManageTariffs,),
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


@extend_schema(tags=['tariffs'])
class TariffViewSet(_CrudViewSet):
    serializer_class = TariffSerializer
    service = TariffService
    filterset_fields = ('from_city', 'to_city', 'is_active')
    search_fields = ('name', 'code')
    ordering_fields = ('name', 'base_price', 'created_at')

    def get_queryset(self):
        return TariffSelector.list()


@extend_schema(tags=['tariffs'])
class AdditionalServiceViewSet(_CrudViewSet):
    serializer_class = AdditionalServiceSerializer
    service = AdditionalServiceService
    filterset_fields = ('is_active',)
    search_fields = ('name', 'code')
    ordering_fields = ('name', 'price')

    def get_queryset(self):
        return TariffSelector.services()


class TariffCalculateView(APIView):
    """Калькулятор стоимости доставки — доступен всем авторизованным,
    включая клиентов (ТЗ, раздел 15: расчёт стоимости в Client App)."""

    @extend_schema(
        request=TariffCalculationRequestSerializer,
        responses=TariffCalculationResponseSerializer,
        summary='Расчёт стоимости доставки',
        tags=['tariffs'],
    )
    def post(self, request):
        serializer = TariffCalculationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = TariffService.calculate(**serializer.validated_data)
        return Response(TariffCalculationResponseSerializer(result).data)
