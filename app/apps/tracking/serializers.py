from rest_framework import serializers

from apps.tracking.models import TrackingEvent


class TrackingEventSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True, default=None)

    class Meta:
        model = TrackingEvent
        fields = (
            'id',
            'order',
            'package',
            'status',
            'latitude',
            'longitude',
            'comment',
            'employee',
            'employee_name',
            'created_at',
        )
        read_only_fields = fields
