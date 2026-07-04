from django.contrib import admin

from apps.gps.models import Geofence, GPSEvent, GPSLog


@admin.register(GPSLog)
class GPSLogAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'shipment', 'latitude', 'longitude', 'speed', 'server_time')
    list_filter = ('vehicle',)
    readonly_fields = [field.name for field in GPSLog._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(GPSEvent)
class GPSEventAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'shipment', 'type', 'created_at')
    list_filter = ('type',)
    readonly_fields = [field.name for field in GPSEvent._meta.fields]

    def has_add_permission(self, request) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Geofence)
class GeofenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'latitude', 'longitude', 'radius_m', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')
