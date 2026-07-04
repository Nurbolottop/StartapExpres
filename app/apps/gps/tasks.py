"""Фоновые проверки GPS (ТЗ, разделы 04, 10, 20, 22).

Расписание — CELERY_BEAT_SCHEDULE в settings: активные рейсы каждые 30 сек,
потеря связи каждые 5 минут.
"""

from datetime import timedelta

from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

from apps.common import events


@shared_task(name='gps.check_offline_vehicles')
def check_offline_vehicles() -> int:
    """Нет координат 10 мин → уведомление; 60 мин → рейс GPS_LOST (ТЗ, раздел 22)."""
    from apps.gps.models import GPSLog
    from apps.gps.services import OFFLINE_LOST_MINUTES, OFFLINE_NOTIFY_MINUTES
    from apps.shipments.choices import ShipmentStatus
    from apps.shipments.models import Shipment

    now = timezone.now()
    flagged = 0
    active = Shipment.objects.filter(
        status__in=(ShipmentStatus.IN_TRANSIT,), vehicle__isnull=False
    ).select_related('vehicle')

    for shipment in active:
        last = (
            GPSLog.objects.filter(shipment=shipment)
            .order_by('-server_time')
            .values_list('server_time', flat=True)
            .first()
        )
        reference = last or shipment.departure_time or shipment.created_at
        silence = now - reference

        if silence >= timedelta(minutes=OFFLINE_LOST_MINUTES):
            shipment.status = ShipmentStatus.GPS_LOST
            shipment.version += 1
            shipment.save(update_fields=['status', 'version', 'updated_at'])
            events.publish(
                'gps.shipment_lost',
                {
                    'actor_id': None,
                    'model': 'Shipment',
                    'object_id': str(shipment.id),
                    'action': 'gps_lost',
                    'new': {'silence_minutes': int(silence.total_seconds() // 60)},
                },
                source='gps',
            )
            flagged += 1
        elif silence >= timedelta(minutes=OFFLINE_NOTIFY_MINUTES):
            notify_key = f'gps:offline_notified:{shipment.id}'
            if cache.add(notify_key, True, timeout=OFFLINE_NOTIFY_MINUTES * 60):
                events.publish(
                    'gps.offline',
                    {
                        'actor_id': None,
                        'model': 'Shipment',
                        'object_id': str(shipment.id),
                        'action': 'gps_offline',
                        'new': {'silence_minutes': int(silence.total_seconds() // 60)},
                    },
                    source='gps',
                )
                flagged += 1
    return flagged


@shared_task(name='gps.detect_long_stops')
def detect_long_stops() -> int:
    """Скорость < 3 км/ч дольше 30 минут → LONG_STOP (ТЗ, разделы 04, 10)."""
    from apps.gps.choices import GPSEventType
    from apps.gps.models import GPSEvent, GPSLog
    from apps.gps.services import LONG_STOP_MINUTES, STOP_SPEED_KMH
    from apps.shipments.choices import ShipmentStatus
    from apps.shipments.models import Shipment

    now = timezone.now()
    detected = 0
    active = Shipment.objects.filter(status=ShipmentStatus.IN_TRANSIT, vehicle__isnull=False)

    for shipment in active:
        window = GPSLog.objects.filter(
            shipment=shipment, server_time__gte=now - timedelta(minutes=LONG_STOP_MINUTES)
        )
        if not window.exists():
            continue
        if window.filter(speed__gt=STOP_SPEED_KMH).exists():
            continue
        dedup_key = f'gps:long_stop:{shipment.id}'
        if not cache.add(dedup_key, True, timeout=LONG_STOP_MINUTES * 60):
            continue
        last = window.order_by('-server_time').first()
        GPSEvent.objects.create(
            vehicle=shipment.vehicle,
            shipment=shipment,
            type=GPSEventType.LONG_STOP,
            latitude=last.latitude,
            longitude=last.longitude,
            details={'minutes': LONG_STOP_MINUTES},
        )
        events.publish(
            'gps.long_stop',
            {
                'actor_id': None,
                'model': 'Shipment',
                'object_id': str(shipment.id),
                'action': 'gps_long_stop',
                'new': {'minutes': LONG_STOP_MINUTES},
            },
            source='gps',
        )
        detected += 1
    return detected
