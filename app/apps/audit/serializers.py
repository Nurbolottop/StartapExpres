from rest_framework import serializers

from apps.audit.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_phone = serializers.CharField(source='user.phone', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = (
            'id',
            'user',
            'user_phone',
            'role',
            'model',
            'object_uuid',
            'action',
            'event_type',
            'old_data',
            'new_data',
            'ip',
            'user_agent',
            'request_id',
            'created_at',
        )
        read_only_fields = fields
