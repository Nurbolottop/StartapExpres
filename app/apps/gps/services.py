"""Сервисный слой GPS (ТЗ, раздел 10).

Приём координат с валидацией, live-точки в Redis, ETA, детекция
превышения скорости и входа/выхода из геозон. Офлайн- и стоп-детекция —
Celery-задачи (apps.gps.tasks).
"""

import math
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from apps.common import errors, events
from apps.common.exceptions import BusinessException
from apps.gps.choices import GPSEventType
from apps.gps.models import Geofence, GPSEvent, GPSLog
from apps.shipments.choices import STARTED_STATUSES
from apps.shipments.models import Shipment

MAX_ACCURACY_M = 100  # ТЗ, раздел 10: точки хуже 100 м отбрасываются
MAX_POINT_AGE_MINUTES = 5  # ТЗ, раздел 10: точки старше 5 минут отбрасываются
DEFAULT_SPEED_LIMIT_KMH = 90  # ТЗ, раздел 18: настройка GPS (переедет в SystemSettings)
LIVE_TTL_SECONDS = 600
STOP_SPEED_KMH = 3  # ТЗ, раздел 10
OFFLINE_NOTIFY_MINUTES = 10  # ТЗ, разделы 10, 22
OFFLINE_LOST_MINUTES = 60  # ТЗ, раздел 22: рейс -> GPS_LOST
LONG_STOP_MINUTES = 30  # ТЗ, разделы 04, 10


class InvalidCoordinatesException(BusinessException):
    default_code = errors.GPSErrors.INVALID_COORDINATES
    default_message = 'Координаты отклонены: неточные или устаревшие.'


class DeviceNotRegisteredException(BusinessException):
    default_code = errors.GPSErrors.DEVICE_NOT_REGISTERED
    default_message = 'У водителя нет активного рейса для передачи GPS.'


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Расстояние между координатами, км."""
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    radius = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def live_key(vehicle_id) -> str:
    return f'gps:last:{vehicle_id}'


class GPSService:
    @staticmethod
    def validate_point(*, accuracy, device_time) -> None:
        if accuracy is not None and Decimal(accuracy) > MAX_ACCURACY_M:
            raise InvalidCoordinatesException(details={'accuracy': str(accuracy)})
        if device_time < timezone.now() - timedelta(minutes=MAX_POINT_AGE_MINUTES):
            raise InvalidCoordinatesException(
                'Координаты устарели.', details={'device_time': device_time.isoformat()}
            )

    @classmethod
    @transaction.atomic
    def update(
        cls,
        *,
        driver,
        latitude,
        longitude,
        device_time,
        speed=Decimal('0'),
        heading=None,
        altitude=None,
        accuracy=Decimal('0'),
        battery_level=None,
        device_id='',
        app_version='',
    ) -> GPSLog:
        """Приём координат от водителя (ТЗ, разделы 03, 10, 15)."""
        cls.validate_point(accuracy=accuracy, device_time=device_time)

        shipment = (
            Shipment.objects.filter(driver=driver, status__in=STARTED_STATUSES)
            .select_related('vehicle', 'arrival_branch__city', 'route')
            .first()
        )
        if shipment is None or shipment.vehicle_id is None:
            raise DeviceNotRegisteredException()

        previous = cache.get(live_key(shipment.vehicle_id))
        log = GPSLog.objects.create(
            vehicle=shipment.vehicle,
            driver=driver,
            shipment=shipment,
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
            speed=speed,
            heading=heading,
            accuracy=accuracy,
            battery_level=battery_level,
            device_id=device_id,
            app_version=app_version,
            device_time=device_time,
        )

        eta_minutes = cls._calculate_eta(shipment, latitude, longitude, speed)
        cache.set(
            live_key(shipment.vehicle_id),
            {
                'vehicle_id': str(shipment.vehicle_id),
                'shipment_id': str(shipment.id),
                'shipment_number': shipment.shipment_number,
                'latitude': str(latitude),
                'longitude': str(longitude),
                'speed': str(speed),
                'heading': heading,
                'eta_minutes': eta_minutes,
                'updated_at': timezone.now().isoformat(),
            },
            timeout=LIVE_TTL_SECONDS,
        )

        cls._detect_overspeed(shipment, log)
        cls._detect_geofences(shipment, log, previous)
        return log

    @staticmethod
    def _calculate_eta(shipment, latitude, longitude, speed) -> int | None:
        """ETA по прямому расстоянию до города прибытия (ТЗ, раздел 10)."""
        city = shipment.arrival_branch.city
        if city.latitude is None or city.longitude is None:
            return None
        distance_km = haversine_km(latitude, longitude, city.latitude, city.longitude)
        avg_speed = max(float(speed), 30.0)  # не делим на ноль на остановках
        return int(distance_km / avg_speed * 60)

    @staticmethod
    def _record_event(shipment, log, event_type: str, details: dict) -> None:
        GPSEvent.objects.create(
            vehicle=log.vehicle,
            shipment=shipment,
            type=event_type,
            latitude=log.latitude,
            longitude=log.longitude,
            details=details,
        )
        events.publish(
            f'gps.{event_type}',
            {
                'actor_id': str(log.driver_id) if log.driver_id else None,
                'model': 'Shipment',
                'object_id': str(shipment.id),
                'action': f'gps_{event_type}',
                'new': details,
            },
            source='gps',
        )

    @classmethod
    def _detect_overspeed(cls, shipment, log) -> None:
        if float(log.speed) > DEFAULT_SPEED_LIMIT_KMH:
            cls._record_event(
                shipment,
                log,
                GPSEventType.OVERSPEED,
                {'speed': str(log.speed), 'limit': DEFAULT_SPEED_LIMIT_KMH},
            )

    @classmethod
    def _detect_geofences(cls, shipment, log, previous: dict | None) -> None:
        for geofence in Geofence.objects.filter(is_active=True):
            inside_now = (
                haversine_km(log.latitude, log.longitude, geofence.latitude, geofence.longitude) * 1000
                <= geofence.radius_m
            )
            was_inside = False
            if previous:
                was_inside = (
                    haversine_km(
                        previous['latitude'], previous['longitude'], geofence.latitude, geofence.longitude
                    )
                    * 1000
                    <= geofence.radius_m
                )
            if inside_now and not was_inside:
                cls._record_event(shipment, log, GPSEventType.ENTER_GEOFENCE, {'geofence': geofence.name})
            elif was_inside and not inside_now:
                cls._record_event(shipment, log, GPSEventType.EXIT_GEOFENCE, {'geofence': geofence.name})


class GPSSelector:
    @staticmethod
    def live() -> list[dict]:
        """Онлайн-точки всех машин в активных рейсах (ТЗ, раздел 10)."""
        vehicle_ids = Shipment.objects.filter(status__in=STARTED_STATUSES, vehicle__isnull=False).values_list(
            'vehicle_id', flat=True
        )
        points = []
        for vehicle_id in vehicle_ids:
            point = cache.get(live_key(vehicle_id))
            if point:
                points.append(point)
        return points

    @staticmethod
    def history(*, vehicle_id=None, shipment_id=None, date_from=None, date_to=None):
        queryset = GPSLog.objects.all()
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        if shipment_id:
            queryset = queryset.filter(shipment_id=shipment_id)
        if date_from:
            queryset = queryset.filter(server_time__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(server_time__date__lte=date_to)
        return queryset
