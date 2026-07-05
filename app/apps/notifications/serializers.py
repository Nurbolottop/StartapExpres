from rest_framework import serializers

from apps.notifications.choices import NotificationPriority
from apps.notifications.models import Notification, NotificationTemplate


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = (
            'id',
            'title',
            'body',
            'type',
            'priority',
            'status',
            'event_type',
            'is_read',
            'sent_at',
            'created_at',
        )
        read_only_fields = fields


class NotificationSendSerializer(serializers.Serializer):
    user = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    priority = serializers.ChoiceField(
        choices=NotificationPriority.choices, default=NotificationPriority.NORMAL
    )


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ('id', 'name', 'type', 'language', 'title', 'body', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')
