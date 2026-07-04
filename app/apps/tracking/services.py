"""Сервис трекинга: единственная точка записи событий (ТЗ, раздел 10)."""

from apps.tracking.models import TrackingEvent


class TrackingService:
    @staticmethod
    def record(
        *,
        order,
        status: str,
        package=None,
        employee=None,
        comment: str = '',
        latitude=None,
        longitude=None,
    ) -> TrackingEvent:
        return TrackingEvent.objects.create(
            order=order,
            package=package,
            status=status,
            employee=employee,
            comment=comment,
            latitude=latitude,
            longitude=longitude,
        )
