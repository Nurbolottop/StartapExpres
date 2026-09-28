from django.contrib import admin

from apps.shipments.models import Incident, Shipment, ShipmentCheckpoint, ShipmentItem


class ShipmentItemInline(admin.TabularInline):
    model = ShipmentItem
    extra = 0
    readonly_fields = ('order', 'package', 'loaded_at', 'unloaded_at')
    can_delete = False


class ShipmentCheckpointInline(admin.TabularInline):
    model = ShipmentCheckpoint
    extra = 0
    readonly_fields = ('route_point', 'reached_at', 'comment', 'created_by', 'created_at')
    fields = readonly_fields
    can_delete = False


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'shipment_number',
        'status',
        'vehicle',
        'driver',
        'departure_branch',
        'arrival_branch',
        'planned_departure',
    )
    list_filter = ('status', 'departure_branch', 'arrival_branch')
    search_fields = ('shipment_number', 'vehicle__plate_number', 'driver__phone')
    readonly_fields = ('id', 'shipment_number', 'status', 'version', 'created_at', 'updated_at')
    inlines = (ShipmentItemInline, ShipmentCheckpointInline)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('shipment', 'type', 'created_by', 'created_at')
    list_filter = ('type',)
    search_fields = ('shipment__shipment_number', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
