from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

_HEALTH_RESPONSE = inline_serializer(
    name='HealthCheckResponse',
    fields={'status': serializers.CharField(), 'component': serializers.CharField()},
)


def _check_database() -> bool:
    try:
        connections['default'].cursor()
        return True
    except OperationalError:
        return False


def _check_cache() -> bool:
    try:
        cache.set('health_check', '1', timeout=5)
        return cache.get('health_check') == '1'
    except Exception:
        return False


def _check_celery() -> bool:
    try:
        from core.celery import app as celery_app

        return bool(celery_app.control.ping(timeout=1.0))
    except Exception:
        return False


def _check_storage() -> bool:
    import tempfile

    from django.core.files.storage import default_storage

    try:
        with tempfile.NamedTemporaryFile() as probe:
            probe.write(b'ok')
            probe.seek(0)
            name = default_storage.save('health/probe.txt', probe)
        default_storage.delete(name)
        return True
    except Exception:
        return False


class BaseHealthView(APIView):
    """Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()
    component = 'system'
    checks: tuple = ()

    @extend_schema(responses={200: _HEALTH_RESPONSE}, tags=['health'])
    def get(self, request):
        healthy = all(check() for check in self.checks)
        return Response(
            {'status': 'ok' if healthy else 'error', 'component': self.component},
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class HealthView(BaseHealthView):
    component = 'system'
    checks = (_check_database, _check_cache)


class DatabaseHealthView(BaseHealthView):
    component = 'database'
    checks = (_check_database,)


class CacheHealthView(BaseHealthView):
    component = 'cache'
    checks = (_check_cache,)


class RedisHealthView(BaseHealthView):
    component = 'redis'
    checks = (_check_cache,)


class CeleryHealthView(BaseHealthView):
    component = 'celery'
    checks = (_check_celery,)


class StorageHealthView(BaseHealthView):
    component = 'storage'
    checks = (_check_storage,)
