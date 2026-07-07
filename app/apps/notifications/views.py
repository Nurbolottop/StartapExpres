from django.utils.translation import gettext as _
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.exceptions import NotFoundException
from apps.common.permissions import ActionPermissionsMixin, RolePermission
from apps.notifications.choices import NotificationStatus, NotificationType
from apps.notifications.models import Device, Notification, NotificationTemplate
from apps.notifications.serializers import (
    DeviceRegisterSerializer,
    DeviceSerializer,
    NotificationSendSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
)
from apps.notifications.services import DeviceService, NotificationService
from apps.users.choices import Roles


class DeviceRegisterView(APIView):
    """Привязка FCM/APNs-токена устройства к пользователю (push-уведомления)."""

    @extend_schema(
        request=DeviceRegisterSerializer,
        responses={201: DeviceSerializer},
        summary='Регистрация push-токена устройства',
        tags=['auth'],
    )
    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = DeviceService.register(user=request.user, **serializer.validated_data)
        return Response(DeviceSerializer(device).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses=DeviceSerializer(many=True),
        summary='Мои push-устройства',
        tags=['auth'],
    )
    def get(self, request):
        devices = Device.objects.filter(user=request.user, is_active=True)
        return Response(DeviceSerializer(devices, many=True).data)


class DeviceUnregisterView(APIView):
    """Отвязка push-токена (вызывается при logout)."""

    @extend_schema(
        responses={204: None},
        summary='Удаление push-токена устройства',
        tags=['auth'],
    )
    def delete(self, request, device_id: str):
        if not DeviceService.unregister(user=request.user, device_id=device_id):
            raise NotFoundException(_('Устройство не найдено.'))
        return Response(status=status.HTTP_204_NO_CONTENT)


class CanSendNotifications(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)


class CanManageTemplates(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR)


@extend_schema(tags=['notifications'])
class NotificationViewSet(ActionPermissionsMixin, ReadOnlyModelViewSet):
    """Свои уведомления (ТЗ, раздел 03): список, отметка о прочтении."""

    serializer_class = NotificationSerializer
    filterset_fields = ('type', 'is_read', 'status')
    ordering_fields = ('created_at',)

    permission_classes_by_action = {
        '__default__': (IsAuthenticated,),
        'send': (CanSendNotifications,),
    }

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @extend_schema(request=None, responses=NotificationSerializer, summary='Отметить прочитанным')
    @action(detail=True, methods=['patch'])
    def read(self, request, pk=None):
        notification = NotificationService.mark_read(user=request.user, notification=self.get_object())
        return Response(NotificationSerializer(notification).data)

    @extend_schema(
        request=NotificationSendSerializer,
        responses={201: NotificationSerializer},
        summary='Отправить уведомление пользователю',
    )
    @action(detail=False, methods=['post'])
    def send(self, request):
        from apps.common.exceptions import NotFoundException
        from apps.notifications.tasks import deliver_notification
        from apps.users.models import User

        serializer = NotificationSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = User.objects.filter(id=data['user']).first()
        if user is None:
            raise NotFoundException(_('Получатель не найден.'))
        notification = Notification.objects.create(
            user=user,
            title=data['title'],
            body=data['body'],
            priority=data['priority'],
            type=NotificationType.IN_APP,
            status=NotificationStatus.QUEUED,
            created_by=request.user,
        )
        deliver_notification.delay(str(notification.id))
        return Response(NotificationSerializer(notification).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=['notifications'])
class NotificationTemplateViewSet(ActionPermissionsMixin, ModelViewSet):
    serializer_class = NotificationTemplateSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_fields = ('type', 'language', 'is_active')
    search_fields = ('name', 'title')

    permission_classes_by_action = {
        '__default__': (CanManageTemplates,),
    }

    def get_queryset(self):
        return NotificationTemplate.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        instance.delete()
