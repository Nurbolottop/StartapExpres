from django.contrib import admin

from apps.vehicles.models import Vehicle, VehicleType


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'max_weight', 'max_volume', 'axle_count', 'is_active')
    search_fields = ('name', 'code')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = (
        'plate_number',
        'brand',
        'model',
        'vehicle_type',
        'branch',
        'status',
        'current_driver',
        'is_active',
    )
    list_filter = ('status', 'fuel_type', 'branch', 'is_active')
    search_fields = ('plate_number', 'brand', 'model', 'vin')
    readonly_fields = ('id', 'created_at', 'updated_at')
