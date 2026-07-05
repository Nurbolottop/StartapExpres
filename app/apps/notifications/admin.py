from django.contrib import admin

from apps.notifications.models import Notification, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'type', 'status', 'is_read', 'retry_count', 'created_at')
    list_filter = ('type', 'status', 'is_read')
    search_fields = ('title', 'user__phone', 'event_type')
    readonly_fields = [field.name for field in Notification._meta.fields]


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'language', 'title', 'is_active')
    list_filter = ('type', 'language', 'is_active')
    search_fields = ('name', 'title')
    readonly_fields = ('id', 'created_at', 'updated_at')
