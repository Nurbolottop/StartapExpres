from rest_framework import serializers

from apps.shipments.choices import IncidentType
from apps.shipments.models import Incident, Shipment, ShipmentItem, ShipmentStatusHistory


class ShipmentItemSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    package_title = serializers.CharField(source='package.title', read_only=True)
    qr_code = serializers.CharField(source='package.qr_code', read_only=True)

    class Meta:
        model = ShipmentItem
        fields = (
            'id',
            'order',
            'order_number',
            'package',
            'package_title',
            'qr_code',
            'loaded_at',
            'unloaded_at',
        )
        read_only_fields = fields


class ShipmentSerializer(serializers.ModelSerializer):
    vehicle_plate = serializers.CharField(source='vehicle.plate_number', read_only=True, default=None)
    driver_name = serializers.CharField(source='driver.full_name', read_only=True, default=None)
    route_code = serializers.CharField(source='route.code', read_only=True, default=None)
    departure_branch_name = serializers.CharField(source='departure_branch.name', read_only=True)
    arrival_branch_name = serializers.CharField(source='arrival_branch.name', read_only=True)
    items = ShipmentItemSerializer(many=True, read_only=True)

    class Meta:
        model = Shipment
        fields = (
            'id',
            'shipment_number',
            'vehicle',
            'vehicle_plate',
            'driver',
            'driver_name',
            'route',
            'route_code',
            'departure_branch',
            'departure_branch_name',
            'arrival_branch',
            'arrival_branch_name',
            'planned_departure',
            'departure_time',
            'arrival_time',
            'status',
            'version',
            'items',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class ShipmentCreateSerializer(serializers.Serializer):
    departure_branch = serializers.UUIDField()
    arrival_branch = serializers.UUIDField()
    route = serializers.UUIDField(required=False, allow_null=True, default=None)
    vehicle = serializers.UUIDField(required=False, allow_null=True, default=None)
    driver = serializers.UUIDField(required=False, allow_null=True, default=None)
    planned_departure = serializers.DateTimeField(required=False, allow_null=True, default=None)

    def validate(self, attrs):
        from apps.branches.models import Branch
        from apps.routes.models import Route
        from apps.users.models import User
        from apps.vehicles.models import Vehicle

        def resolve(model, value, label):
            if value is None:
                return None
            instance = model.objects.filter(id=value).first()
            if instance is None:
                raise serializers.ValidationError({label: 'Не найдено.'})
            return instance

        attrs['departure_branch'] = resolve(Branch, attrs['departure_branch'], 'departure_branch')
        attrs['arrival_branch'] = resolve(Branch, attrs['arrival_branch'], 'arrival_branch')
        attrs['route'] = resolve(Route, attrs.get('route'), 'route')
        attrs['vehicle'] = resolve(Vehicle, attrs.get('vehicle'), 'vehicle')
        attrs['driver'] = resolve(User, attrs.get('driver'), 'driver')
        return attrs


class AssignSerializer(serializers.Serializer):
    id = serializers.UUIDField()


class OrderRefSerializer(serializers.Serializer):
    order = serializers.UUIDField()


class ShipmentScanSerializer(serializers.Serializer):
    qr_code = serializers.CharField(max_length=64)


class IncidentCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=IncidentType.choices)
    description = serializers.CharField()
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True, default=None
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True, default=None
    )


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = (
            'id',
            'shipment',
            'type',
            'description',
            'photo',
            'latitude',
            'longitude',
            'created_by',
            'created_at',
        )
        read_only_fields = fields


class ShipmentStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShipmentStatusHistory
        fields = ('id', 'from_status', 'to_status', 'changed_by', 'comment', 'created_at')
        read_only_fields = fields
