import django_filters

from apps.audit.models import AuditLog


class AuditLogFilter(django_filters.FilterSet):
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = AuditLog
        fields = ('user', 'model', 'action', 'event_type', 'ip')
