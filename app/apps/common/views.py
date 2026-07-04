from django.core.cache import cache
from django.db import connections
from django.db.utils import OperationalError
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """Проверка живости сервиса и его зависимостей (БД, кэш)."""

    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = ()

    @extend_schema(
        responses={
            200: inline_serializer(
                name='HealthCheckResponse',
                fields={
                    'status': serializers.CharField(),
                    'database': serializers.BooleanField(),
                    'cache': serializers.BooleanField(),
                },
            ),
        },
        summary='Health check',
        tags=['health'],
    )
    def get(self, request):
        database_ok = True
        cache_ok = True

        try:
            connections['default'].cursor()
        except OperationalError:
            database_ok = False

        try:
            cache.set('health_check', '1', timeout=5)
            cache_ok = cache.get('health_check') == '1'
        except Exception:
            cache_ok = False

        healthy = database_ok and cache_ok
        return Response(
            {
                'status': 'ok' if healthy else 'degraded',
                'database': database_ok,
                'cache': cache_ok,
            },
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
