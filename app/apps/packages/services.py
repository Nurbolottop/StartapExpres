"""Сервисный слой packages: QR, фото, сканирование (ТЗ, разделы 07–08).

Складские операции (приём/размещение/погрузка) — Этап 3.
"""

import uuid

from django.db import transaction
from django.utils import timezone

from apps.common import events
from apps.orders.choices import SHIPPED_STATUSES
from apps.packages import exceptions
from apps.packages.models import Package, PackagePhoto
from apps.tracking.services import TrackingService


class PackageService:
    @staticmethod
    @transaction.atomic
    def add(*, actor, order, data: dict) -> Package:
        if order.status in SHIPPED_STATUSES:
            raise exceptions.PackageLockedException()
        package = Package(order=order, created_by=actor, **data)
        package.full_clean()
        package.save()
        events.publish(
            'package.created',
            {
                'actor_id': str(actor.id),
                'model': 'Package',
                'object_id': str(package.id),
                'action': 'create',
                'new': {'title': package.title, 'order': order.order_number},
            },
            source='packages',
        )
        return package

    @staticmethod
    @transaction.atomic
    def update(*, actor, package: Package, data: dict) -> Package:
        if package.order.status in SHIPPED_STATUSES:
            raise exceptions.PackageLockedException()
        old = {field: str(getattr(package, field)) for field in data}
        for field, value in data.items():
            setattr(package, field, value)
        package.updated_by = actor
        package.full_clean()
        package.save()
        events.publish(
            'package.updated',
            {
                'actor_id': str(actor.id),
                'model': 'Package',
                'object_id': str(package.id),
                'action': 'update',
                'old': old,
                'new': {field: str(getattr(package, field)) for field in old},
            },
            source='packages',
        )
        return package

    @staticmethod
    @transaction.atomic
    def soft_delete(*, actor, package: Package) -> None:
        if package.order.status in SHIPPED_STATUSES:
            raise exceptions.PackageLockedException()
        package.updated_by = actor
        package.is_active = False
        package.save(update_fields=['updated_by', 'is_active', 'updated_at'])
        package.delete()
        events.publish(
            'package.deleted',
            {
                'actor_id': str(actor.id),
                'model': 'Package',
                'object_id': str(package.id),
                'action': 'soft_delete',
            },
            source='packages',
        )

    @staticmethod
    @transaction.atomic
    def generate_qr(*, actor, package: Package) -> Package:
        """QR создаётся один раз; повторная генерация запрещена (ТЗ, разделы 06, 08)."""
        locked = Package.objects.select_for_update().get(id=package.id)
        if locked.qr_code:
            raise exceptions.QRAlreadyGeneratedException()
        locked.qr_code = uuid.uuid4().hex
        locked.barcode = f'{uuid.uuid4().int % 10**12:012d}'
        locked.qr_generated_at = timezone.now()
        locked.updated_by = actor
        locked.save(update_fields=['qr_code', 'barcode', 'qr_generated_at', 'updated_by', 'updated_at'])
        TrackingService.record(order=locked.order, package=locked, status='qr_generated', employee=actor)
        events.publish(
            'package.qr_generated',
            {
                'actor_id': str(actor.id),
                'model': 'Package',
                'object_id': str(locked.id),
                'action': 'generate_qr',
                'new': {'qr_code': locked.qr_code},
            },
            source='packages',
        )
        return locked

    @staticmethod
    def scan(*, actor, qr_code: str) -> Package:
        """Сканирование QR: фиксирует событие трекинга (ТЗ, раздел 03)."""
        package = Package.objects.select_related('order').filter(qr_code=qr_code).first()
        if package is None:
            raise exceptions.PackageNotFoundByQRException()
        TrackingService.record(order=package.order, package=package, status='scanned', employee=actor)
        events.publish(
            'package.scanned',
            {'actor_id': str(actor.id), 'model': 'Package', 'object_id': str(package.id), 'action': 'scan'},
            source='packages',
        )
        return package

    @staticmethod
    @transaction.atomic
    def upload_photo(*, actor, package: Package, image, photo_type: str) -> PackagePhoto:
        photo = PackagePhoto(
            package=package, image=image, type=photo_type, uploaded_by=actor, created_by=actor
        )
        photo.full_clean()
        photo.save()
        events.publish(
            'package.photo_uploaded',
            {
                'actor_id': str(actor.id),
                'model': 'PackagePhoto',
                'object_id': str(photo.id),
                'action': 'upload_photo',
                'new': {'type': photo_type},
            },
            source='packages',
        )
        return photo
