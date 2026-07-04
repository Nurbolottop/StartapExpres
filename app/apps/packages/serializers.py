from decimal import Decimal

from rest_framework import serializers

from apps.packages.choices import PhotoType
from apps.packages.models import Package, PackagePhoto


class PackagePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackagePhoto
        fields = ('id', 'package', 'image', 'type', 'uploaded_by', 'created_at')
        read_only_fields = ('id', 'package', 'uploaded_by', 'created_at')


class PackageSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)

    class Meta:
        model = Package
        fields = (
            'id',
            'order',
            'order_number',
            'qr_code',
            'barcode',
            'title',
            'description',
            'weight',
            'length',
            'width',
            'height',
            'volume',
            'declared_price',
            'fragile',
            'dangerous',
            'status',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'order', 'qr_code', 'barcode', 'status', 'created_at', 'updated_at')


class PackageWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    weight = serializers.DecimalField(max_digits=10, decimal_places=3, min_value=Decimal('0.001'))
    length = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)
    width = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)
    height = serializers.IntegerField(min_value=1, required=False, allow_null=True, default=None)
    volume = serializers.DecimalField(max_digits=10, decimal_places=3, min_value=0, required=False, default=0)
    declared_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=0, required=False, default=0
    )
    fragile = serializers.BooleanField(default=False)
    dangerous = serializers.BooleanField(default=False)


class PackagePhotoUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()
    type = serializers.ChoiceField(choices=PhotoType.choices)


class PackageScanSerializer(serializers.Serializer):
    qr_code = serializers.CharField(max_length=64)
