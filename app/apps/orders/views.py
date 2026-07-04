from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.idempotency import idempotent
from apps.common.permissions import ActionPermissionsMixin, IsOwner
from apps.orders import permissions as order_permissions
from apps.orders.filters import OrderFilter
from apps.orders.selectors import OrderSelector
from apps.orders.serializers import (
    OrderCancelSerializer,
    OrderCorrectionSerializer,
    OrderCreateSerializer,
    OrderPaySerializer,
    OrderSerializer,
    OrderStatusChangeSerializer,
    OrderStatusHistorySerializer,
    OrderUpdateSerializer,
)
from apps.orders.services import OrderService
from apps.orders.transitions import OrderTransitionService
from apps.tracking.serializers import TrackingEventSerializer
from apps.users.choices import Roles


class OrderOwnerPermission(IsOwner):
    """Клиент работает только со своими заказами (object-level)."""

    owner_fields = ('client',)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.role == Roles.CLIENT:
            return obj.client_id == request.user.id
        return True


@extend_schema(tags=['orders'])
class OrderViewSet(ActionPermissionsMixin, ModelViewSet):
    """Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete."""

    serializer_class = OrderSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_class = OrderFilter
    search_fields = (
        'order_number',
        'sender_name',
        'sender_phone',
        'receiver_name',
        'receiver_phone',
        'client__phone',
    )
    ordering_fields = ('created_at', 'total_price', 'status')

    permission_classes_by_action = {
        '__default__': (order_permissions.CanViewOrders, OrderOwnerPermission),
        'create': (order_permissions.CanCreateOrder,),
        'partial_update': (order_permissions.CanEditOrder, OrderOwnerPermission),
        'destroy': (order_permissions.CanCancelOrder, OrderOwnerPermission),
        'submit': (order_permissions.CanEditOrder, OrderOwnerPermission),
        'confirm': (order_permissions.CanConfirmOrder,),
        'need_correction': (order_permissions.CanConfirmOrder,),
        'cancel': (order_permissions.CanCancelOrder, OrderOwnerPermission),
        'pay': (order_permissions.CanPayOrder,),
        'change_status': (order_permissions.CanChangeOrderStatus,),
        'history': (order_permissions.CanViewOrders, OrderOwnerPermission),
        'tracking': (order_permissions.CanViewOrders, OrderOwnerPermission),
    }

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            from apps.orders.models import Order

            return Order.objects.none()
        return OrderSelector.for_user(self.request.user)

    @extend_schema(
        request=OrderCreateSerializer,
        responses={201: OrderSerializer},
        summary='Создание заказа (клиент или оператор)',
    )
    @idempotent
    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        client = data.pop('client', None)
        if request.user.role == Roles.CLIENT or client is None:
            client = request.user
        order = OrderService.create(actor=request.user, client=client, **data)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=OrderUpdateSerializer, responses=OrderSerializer, summary='Редактирование (до отправки)'
    )
    def partial_update(self, request, *args, **kwargs):
        serializer = OrderUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.update(
            actor=request.user, order=self.get_object(), data=serializer.validated_data
        )
        return Response(OrderSerializer(order).data)

    @extend_schema(responses={204: None}, summary='Отмена заказа (soft: статус CANCELLED)')
    def destroy(self, request, *args, **kwargs):
        OrderService.cancel(actor=request.user, order=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None, responses=OrderSerializer, summary='Отправить на проверку')
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        order = OrderService.submit(actor=request.user, order=self.get_object())
        return Response(OrderSerializer(order).data)

    @extend_schema(request=None, responses=OrderSerializer, summary='Подтвердить заказ')
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = OrderService.confirm(actor=request.user, order=self.get_object())
        return Response(OrderSerializer(order).data)

    @extend_schema(
        request=OrderCorrectionSerializer, responses=OrderSerializer, summary='Вернуть на исправление'
    )
    @action(detail=True, methods=['post'], url_path='need-correction')
    def need_correction(self, request, pk=None):
        serializer = OrderCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.need_correction(
            actor=request.user, order=self.get_object(), **serializer.validated_data
        )
        return Response(OrderSerializer(order).data)

    @extend_schema(request=OrderCancelSerializer, responses=OrderSerializer, summary='Отменить заказ')
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        serializer = OrderCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.cancel(actor=request.user, order=self.get_object(), **serializer.validated_data)
        return Response(OrderSerializer(order).data)

    @extend_schema(request=OrderPaySerializer, responses=OrderSerializer, summary='Зафиксировать оплату')
    @idempotent
    @action(detail=True, methods=['post'])
    def pay(self, request, pk=None):
        serializer = OrderPaySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = OrderService.pay(actor=request.user, order=self.get_object(), **serializer.validated_data)
        return Response(OrderSerializer(order).data)

    @extend_schema(
        request=OrderStatusChangeSerializer, responses=OrderSerializer, summary='Изменить статус (FSM)'
    )
    @action(detail=True, methods=['post'], url_path='status')
    def change_status(self, request, pk=None):
        serializer = OrderStatusChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        order = OrderTransitionService.change(
            order=self.get_object(),
            to_status=data['status'],
            actor=request.user,
            comment=data['comment'],
            expected_version=data['version'],
        )
        return Response(OrderSerializer(order).data)

    @extend_schema(responses=OrderStatusHistorySerializer(many=True), summary='История статусов')
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        history = OrderTransitionService.history(self.get_object())
        return Response(OrderStatusHistorySerializer(history, many=True).data)

    @extend_schema(responses=TrackingEventSerializer(many=True), summary='Трекинг заказа')
    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        order = self.get_object()
        trail = order.tracking_events.select_related('employee').all()
        return Response(TrackingEventSerializer(trail, many=True).data)
