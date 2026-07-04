from rest_framework import serializers

from apps.warehouses.models import Warehouse, WarehouseCell, WarehouseZone


class WarehouseSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)
    manager_name = serializers.CharField(source='manager.full_name', read_only=True, default=None)

    class Meta:
        model = Warehouse
        fields = (
            'id',
            'branch',
            'branch_name',
            'name',
            'code',
            'address',
            'manager',
            'manager_name',
            'phone',
            'total_area',
            'max_weight',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class WarehouseZoneSerializer(serializers.ModelSerializer):
    warehouse_code = serializers.CharField(source='warehouse.code', read_only=True)

    class Meta:
        model = WarehouseZone
        fields = (
            'id',
            'warehouse',
            'warehouse_code',
            'name',
            'code',
            'type',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class WarehouseCellSerializer(serializers.ModelSerializer):
    zone_code = serializers.CharField(source='zone.code', read_only=True)
    warehouse_code = serializers.CharField(source='zone.warehouse.code', read_only=True)
    free_weight = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    free_volume = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)

    class Meta:
        model = WarehouseCell
        fields = (
            'id',
            'zone',
            'zone_code',
            'warehouse_code',
            'code',
            'shelf',
            'row',
            'level',
            'capacity_weight',
            'capacity_volume',
            'occupied_weight',
            'occupied_volume',
            'free_weight',
            'free_volume',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'occupied_weight', 'occupied_volume', 'created_at', 'updated_at')
