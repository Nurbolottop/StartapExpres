from rest_framework import serializers

from apps.vehicles.models import Vehicle, VehicleType


class VehicleTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleType
        fields = (
            'id',
            'name',
            'code',
            'max_weight',
            'max_volume',
            'axle_count',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class VehicleSerializer(serializers.ModelSerializer):
    vehicle_type_name = serializers.CharField(source='vehicle_type.name', read_only=True)
    branch_name = serializers.CharField(source='branch.name', read_only=True, default=None)
    driver_phone = serializers.CharField(source='current_driver.phone', read_only=True, default=None)
    driver_name = serializers.CharField(source='current_driver.full_name', read_only=True, default=None)

    class Meta:
        model = Vehicle
        fields = (
            'id',
            'vehicle_type',
            'vehicle_type_name',
            'branch',
            'branch_name',
            'plate_number',
            'vin',
            'brand',
            'model',
            'year',
            'color',
            'max_weight',
            'max_volume',
            'fuel_type',
            'mileage',
            'status',
            'current_driver',
            'driver_phone',
            'driver_name',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'current_driver', 'created_at', 'updated_at')


class AssignDriverSerializer(serializers.Serializer):
    driver = serializers.UUIDField()

    def validate_driver(self, value):
        from apps.users.models import User

        driver = User.objects.filter(id=value).select_related('driver_profile').first()
        if driver is None:
            raise serializers.ValidationError('Водитель не найден.')
        return driver
