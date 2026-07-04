"""API складских операций (ТЗ, раздел 08)."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import RolePermission
from apps.packages.exceptions import PackageNotFoundByQRException
from apps.packages.models import Package
from apps.packages.serializers import PackageSerializer
from apps.users.choices import Roles
from apps.warehouses import serializers_ops as ops
from apps.warehouses.models import InventorySession, WarehouseCell
from apps.warehouses.operations import (
    DeliveryService,
    InventoryService,
    WarehouseOperationsService,
)


class CanOperateWarehouse(RolePermission):
    """Складские операции — склад и руководство (ТЗ, раздел 14)."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.WAREHOUSE)


class CanIssueOrder(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.WAREHOUSE, Roles.OPERATOR)


def _package_by_qr(qr_code: str) -> Package:
    package = Package.objects.select_related('order').filter(qr_code=qr_code).first()
    if package is None:
        raise PackageNotFoundByQRException()
    return package


def _cell(cell_id) -> WarehouseCell:
    from apps.common.exceptions import NotFoundException

    cell = WarehouseCell.objects.filter(id=cell_id, is_active=True).first()
    if cell is None:
        raise NotFoundException('Ячейка не найдена.')
    return cell


class _OpsView(APIView):
    permission_classes = (CanOperateWarehouse,)


@extend_schema(tags=['warehouse-operations'])
class ReceiveView(_OpsView):
    @extend_schema(request=ops.QRSerializer, responses=PackageSerializer, summary='Принять груз')
    def post(self, request):
        serializer = ops.QRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        package = _package_by_qr(serializer.validated_data['qr_code'])
        package = WarehouseOperationsService.receive(actor=request.user, package=package)
        return Response(PackageSerializer(package).data)


@extend_schema(tags=['warehouse-operations'])
class CheckView(_OpsView):
    @extend_schema(
        request=ops.CheckSerializer, responses=PackageSerializer, summary='Проверить, взвесить, обмерить'
    )
    def post(self, request):
        serializer = ops.CheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        package = _package_by_qr(data.pop('qr_code'))
        package = WarehouseOperationsService.check(actor=request.user, package=package, **data)
        return Response(PackageSerializer(package).data)


@extend_schema(tags=['warehouse-operations'])
class StoreView(_OpsView):
    @extend_schema(request=ops.StoreSerializer, responses=PackageSerializer, summary='Разместить в ячейку')
    def post(self, request):
        serializer = ops.StoreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        package = _package_by_qr(data['qr_code'])
        package = WarehouseOperationsService.store(
            actor=request.user, package=package, cell=_cell(data['cell']), reason=data['reason']
        )
        return Response(PackageSerializer(package).data)


@extend_schema(tags=['warehouse-operations'])
class MoveView(_OpsView):
    @extend_schema(
        request=ops.MoveSerializer, responses=PackageSerializer, summary='Переместить между ячейками'
    )
    def post(self, request):
        serializer = ops.MoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        package = _package_by_qr(data['qr_code'])
        package = WarehouseOperationsService.move(
            actor=request.user, package=package, to_cell=_cell(data['to_cell']), reason=data['reason']
        )
        return Response(PackageSerializer(package).data)


@extend_schema(tags=['warehouse-operations'])
class DamageReportView(_OpsView):
    @extend_schema(
        request=ops.DamageSerializer, responses={201: ops.DamageReportSerializer}, summary='Акт повреждения'
    )
    def post(self, request):
        serializer = ops.DamageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        package = _package_by_qr(data.pop('qr_code'))
        report = WarehouseOperationsService.report_damage(actor=request.user, package=package, **data)
        return Response(ops.DamageReportSerializer(report).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['warehouse-operations'])
class LostReportView(_OpsView):
    @extend_schema(request=ops.LostSerializer, responses={201: ops.LostReportSerializer}, summary='Акт утери')
    def post(self, request):
        serializer = ops.LostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        package = _package_by_qr(data.pop('qr_code'))
        report = WarehouseOperationsService.report_lost(actor=request.user, package=package, **data)
        return Response(ops.LostReportSerializer(report).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['warehouse-operations'])
class InventoryOpenView(_OpsView):
    @extend_schema(
        request=ops.InventoryOpenSerializer,
        responses={201: ops.InventorySessionSerializer},
        summary='Открыть инвентаризацию',
    )
    def post(self, request):
        from apps.common.exceptions import NotFoundException
        from apps.warehouses.models import Warehouse

        serializer = ops.InventoryOpenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        warehouse = Warehouse.objects.filter(id=serializer.validated_data['warehouse']).first()
        if warehouse is None:
            raise NotFoundException('Склад не найден.')
        session = InventoryService.open(actor=request.user, warehouse=warehouse)
        return Response(ops.InventorySessionSerializer(session).data, status=status.HTTP_201_CREATED)


def _session(session_id) -> InventorySession:
    from apps.common.exceptions import NotFoundException

    session = InventorySession.objects.filter(id=session_id).first()
    if session is None:
        raise NotFoundException('Инвентаризация не найдена.')
    return session


@extend_schema(tags=['warehouse-operations'])
class InventoryScanView(_OpsView):
    @extend_schema(
        request=ops.QRSerializer,
        responses={200: ops.InventorySessionSerializer},
        summary='Скан груза в инвентаризации',
    )
    def post(self, request, session_id):
        serializer = ops.QRSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = _session(session_id)
        InventoryService.scan(
            actor=request.user, session=session, qr_code=serializer.validated_data['qr_code']
        )
        return Response(ops.InventorySessionSerializer(session).data)


@extend_schema(tags=['warehouse-operations'])
class InventoryCloseView(_OpsView):
    @extend_schema(
        request=None,
        responses=ops.InventorySessionSerializer,
        summary='Закрыть инвентаризацию (отчёт о расхождениях)',
    )
    def post(self, request, session_id):
        session = InventoryService.close(actor=request.user, session=_session(session_id))
        return Response(ops.InventorySessionSerializer(session).data)


@extend_schema(tags=['warehouse-operations'])
class OrderIssueView(APIView):
    permission_classes = (CanIssueOrder,)

    @extend_schema(
        request=ops.IssueSerializer,
        responses={201: ops.DeliveryConfirmationSerializer},
        summary='Выдача заказа получателю',
    )
    def post(self, request, order_id):
        from apps.common.exceptions import NotFoundException
        from apps.orders.models import Order

        serializer = ops.IssueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = Order.objects.filter(id=order_id).first()
        if order is None:
            raise NotFoundException('Заказ не найден.')
        confirmation = DeliveryService.issue(actor=request.user, order=order, **serializer.validated_data)
        return Response(ops.DeliveryConfirmationSerializer(confirmation).data, status=status.HTTP_201_CREATED)
