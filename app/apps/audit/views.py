from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.audit.filters import AuditLogFilter
from apps.audit.models import AuditLog
from apps.audit.permissions import CanViewAudit
from apps.audit.serializers import AuditLogSerializer


@extend_schema(tags=['audit'])
class AuditLogViewSet(ReadOnlyModelViewSet):
    """Журнал аудита: только чтение (ТЗ, раздел 12)."""

    serializer_class = AuditLogSerializer
    permission_classes = (CanViewAudit,)
    filterset_class = AuditLogFilter
    search_fields = ('object_uuid', 'action', 'model', 'ip')
    ordering_fields = ('created_at',)

    def get_queryset(self):
        return AuditLog.objects.select_related('user')
