from django.contrib import admin

from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'branch', 'manager', 'is_active')
    list_filter = ('branch', 'is_active')
    search_fields = ('name', 'code', 'address')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(WarehouseZone)
class WarehouseZoneAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'warehouse', 'type', 'is_active')
    list_filter = ('type', 'warehouse', 'is_active')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(WarehouseCell)
class WarehouseCellAdmin(admin.ModelAdmin):
    list_display = (
        'code',
        'zone',
        'capacity_weight',
        'occupied_weight',
        'capacity_volume',
        'occupied_volume',
        'is_active',
    )
    list_filter = ('zone__warehouse', 'is_active')
    search_fields = ('code', 'shelf', 'row')
    readonly_fields = ('id', 'occupied_weight', 'occupied_volume', 'created_at', 'updated_at')
