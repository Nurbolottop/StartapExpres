from django.contrib import admin

from apps.audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'role', 'action', 'model', 'object_uuid', 'ip')
    list_filter = ('action', 'model', 'role')
    search_fields = ('object_uuid', 'user__phone', 'ip', 'request_id')
    readonly_fields = [field.name for field in AuditLog._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
