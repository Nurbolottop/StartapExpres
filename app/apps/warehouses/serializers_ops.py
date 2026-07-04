from decimal import Decimal

from rest_framework import serializers

from apps.warehouses.models import (
    DamageReport,
    DeliveryConfirmation,
    InventorySession,
    LostReport,
    WarehouseMovement,
)


class QRSerializer(serializers.Serializer):
    qr_code = serializers.CharField(max_length=64)


class CheckSerializer(QRSerializer):
    weight = serializers.DecimalField(
        max_digits=10,
        decimal_places=3,
        min_value=Decimal('0.001'),
        required=False,
        allow_null=True,
        default=None,
    )
    length = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)
    width = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)
    height = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)


class StoreSerializer(QRSerializer):
    cell = serializers.UUIDField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class MoveSerializer(QRSerializer):
    to_cell = serializers.UUIDField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class DamageSerializer(QRSerializer):
    description = serializers.CharField()
    reason = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class LostSerializer(QRSerializer):
    description = serializers.CharField()


class InventoryOpenSerializer(serializers.Serializer):
    warehouse = serializers.UUIDField()


class IssueSerializer(serializers.Serializer):
    received_by_name = serializers.CharField(max_length=255)
    document_number = serializers.CharField(max_length=100)
    qr_codes = serializers.ListField(child=serializers.CharField(max_length=64), min_length=1)


class WarehouseMovementSerializer(serializers.ModelSerializer):
    from_cell_code = serializers.CharField(source='from_cell.code', read_only=True, default=None)
    to_cell_code = serializers.CharField(source='to_cell.code', read_only=True, default=None)

    class Meta:
        model = WarehouseMovement
        fields = (
            'id',
            'package',
            'from_cell',
            'from_cell_code',
            'to_cell',
            'to_cell_code',
            'reason',
            'created_by',
            'created_at',
        )
        read_only_fields = fields


class DamageReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = DamageReport
        fields = ('id', 'package', 'description', 'reason', 'created_by', 'created_at')
        read_only_fields = fields


class LostReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = LostReport
        fields = ('id', 'package', 'description', 'created_by', 'created_at')
        read_only_fields = fields


class InventorySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventorySession
        fields = ('id', 'warehouse', 'finished_at', 'report', 'created_by', 'created_at')
        read_only_fields = fields


class DeliveryConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryConfirmation
        fields = (
            'id',
            'order',
            'received_by_name',
            'document_number',
            'signature',
            'created_by',
            'created_at',
        )
        read_only_fields = fields
