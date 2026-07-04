from decimal import Decimal

from rest_framework import serializers

from apps.gps.models import Geofence, GPSEvent, GPSLog


class GPSUpdateSerializer(serializers.Serializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6)
    lng = serializers.DecimalField(max_digits=9, decimal_places=6)
    speed = serializers.DecimalField(
        max_digits=5, decimal_places=1, min_value=Decimal('0'), required=False, default=Decimal('0')
    )
    heading = serializers.IntegerField(
        min_value=0, max_value=359, required=False, allow_null=True, default=None
    )
    altitude = serializers.DecimalField(
        max_digits=7, decimal_places=1, required=False, allow_null=True, default=None
    )
    accuracy = serializers.DecimalField(
        max_digits=6, decimal_places=1, min_value=Decimal('0'), required=False, default=Decimal('0')
    )
    battery_level = serializers.IntegerField(
        min_value=0, max_value=100, required=False, allow_null=True, default=None
    )
    device_time = serializers.DateTimeField()
    device_id = serializers.CharField(max_length=64, required=False, allow_blank=True, default='')
    app_version = serializers.CharField(max_length=20, required=False, allow_blank=True, default='')


class GPSLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSLog
        fields = (
            'id',
            'vehicle',
            'driver',
            'shipment',
            'latitude',
            'longitude',
            'altitude',
            'speed',
            'heading',
            'accuracy',
            'battery_level',
            'device_time',
            'server_time',
        )
        read_only_fields = fields


class GPSEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPSEvent
        fields = ('id', 'vehicle', 'shipment', 'type', 'latitude', 'longitude', 'details', 'created_at')
        read_only_fields = fields


class GeofenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geofence
        fields = (
            'id',
            'name',
            'type',
            'latitude',
            'longitude',
            'radius_m',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class LivePointSerializer(serializers.Serializer):
    vehicle_id = serializers.CharField(read_only=True)
    shipment_id = serializers.CharField(read_only=True)
    shipment_number = serializers.CharField(read_only=True)
    latitude = serializers.CharField(read_only=True)
    longitude = serializers.CharField(read_only=True)
    speed = serializers.CharField(read_only=True)
    heading = serializers.IntegerField(read_only=True, allow_null=True)
    eta_minutes = serializers.IntegerField(read_only=True, allow_null=True)
    updated_at = serializers.CharField(read_only=True)
