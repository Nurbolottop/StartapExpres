from rest_framework import serializers

from apps.branches.models import City
from apps.tariffs.models import AdditionalService, Tariff


class TariffSerializer(serializers.ModelSerializer):
    from_city_name = serializers.CharField(source='from_city.name', read_only=True, default=None)
    to_city_name = serializers.CharField(source='to_city.name', read_only=True, default=None)

    class Meta:
        model = Tariff
        fields = (
            'id',
            'name',
            'code',
            'from_city',
            'from_city_name',
            'to_city',
            'to_city_name',
            'base_price',
            'price_per_kg',
            'price_per_m3',
            'min_price',
            'insurance_percent',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class AdditionalServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdditionalService
        fields = ('id', 'name', 'code', 'price', 'description', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class TariffCalculationRequestSerializer(serializers.Serializer):
    from_city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    to_city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())
    weight = serializers.DecimalField(max_digits=10, decimal_places=3, min_value=0)
    volume = serializers.DecimalField(max_digits=10, decimal_places=3, min_value=0, default=0)
    declared_value = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, default=0)
    services = serializers.PrimaryKeyRelatedField(
        queryset=AdditionalService.objects.filter(is_active=True), many=True, required=False, default=list
    )


class TariffCalculationResponseSerializer(serializers.Serializer):
    tariff_code = serializers.CharField(source='tariff.code', read_only=True)
    base_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    weight_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    volume_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    services_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    insurance_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
