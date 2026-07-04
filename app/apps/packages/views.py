from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.common.permissions import ActionPermissionsMixin, IsOwner
from apps.packages import permissions as package_permissions
from apps.packages.selectors import PackageSelector
from apps.packages.serializers import (
    PackagePhotoSerializer,
    PackagePhotoUploadSerializer,
    PackageScanSerializer,
    PackageSerializer,
    PackageWriteSerializer,
)
from apps.packages.services import PackageService
from apps.users.choices import Roles


class PackageOwnerPermission(IsOwner):
    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.role == Roles.CLIENT:
            return obj.order.client_id == request.user.id
        return True


@extend_schema(tags=['packages'])
class PackageViewSet(ActionPermissionsMixin, ModelViewSet):
    """Грузовые места (ТЗ, раздел 03: PACKAGES)."""

    serializer_class = PackageSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_fields = ('order', 'status', 'fragile', 'dangerous')
    search_fields = ('title', 'qr_code', 'barcode', 'order__order_number')
    ordering_fields = ('created_at', 'weight')

    permission_classes_by_action = {
        '__default__': (package_permissions.CanViewPackages, PackageOwnerPermission),
        'create': (package_permissions.CanManagePackages,),
        'partial_update': (package_permissions.CanManagePackages,),
        'destroy': (package_permissions.CanManagePackages,),
        'generate_qr': (package_permissions.CanManagePackages,),
        'scan': (package_permissions.CanScanPackages,),
        'upload_photo': (package_permissions.CanScanPackages,),
    }

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            from apps.packages.models import Package

            return Package.objects.none()
        return PackageSelector.for_user(self.request.user)

    @extend_schema(
        request=PackageWriteSerializer,
        responses={201: PackageSerializer},
        summary='Добавить грузовое место к заказу',
    )
    def create(self, request, *args, **kwargs):
        from apps.orders.selectors import OrderSelector

        serializer = PackageWriteSerializer(data={k: v for k, v in request.data.items() if k != 'order'})
        serializer.is_valid(raise_exception=True)
        order = OrderSelector.for_user(request.user).filter(id=request.data.get('order')).first()
        if order is None:
            from apps.common.exceptions import NotFoundException

            raise NotFoundException('Заказ не найден.')
        package = PackageService.add(actor=request.user, order=order, data=serializer.validated_data)
        return Response(PackageSerializer(package).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=PackageWriteSerializer, responses=PackageSerializer, summary='Изменить грузовое место'
    )
    def partial_update(self, request, *args, **kwargs):
        serializer = PackageWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        package = PackageService.update(
            actor=request.user, package=self.get_object(), data=serializer.validated_data
        )
        return Response(PackageSerializer(package).data)

    @extend_schema(responses={204: None}, summary='Удалить грузовое место (soft)')
    def destroy(self, request, *args, **kwargs):
        PackageService.soft_delete(actor=request.user, package=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(request=None, responses=PackageSerializer, summary='Сгенерировать QR (один раз)')
    @action(detail=True, methods=['post'], url_path='generate-qr')
    def generate_qr(self, request, pk=None):
        package = PackageService.generate_qr(actor=request.user, package=self.get_object())
        return Response(PackageSerializer(package).data)

    @extend_schema(request=PackageScanSerializer, responses=PackageSerializer, summary='Сканировать QR')
    @action(detail=False, methods=['post'])
    def scan(self, request):
        serializer = PackageScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        package = PackageService.scan(actor=request.user, **serializer.validated_data)
        return Response(PackageSerializer(package).data)

    @extend_schema(
        request=PackagePhotoUploadSerializer,
        responses={201: PackagePhotoSerializer},
        summary='Загрузить фото груза',
    )
    @action(
        detail=True, methods=['post'], url_path='upload-photo', parser_classes=(MultiPartParser, FormParser)
    )
    def upload_photo(self, request, pk=None):
        serializer = PackagePhotoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        photo = PackageService.upload_photo(
            actor=request.user,
            package=self.get_object(),
            image=serializer.validated_data['image'],
            photo_type=serializer.validated_data['type'],
        )
        return Response(PackagePhotoSerializer(photo).data, status=status.HTTP_201_CREATED)
