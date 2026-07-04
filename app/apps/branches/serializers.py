from rest_framework import serializers

from apps.branches.models import Branch, City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = (
            'id',
            'name',
            'code',
            'country',
            'latitude',
            'longitude',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class BranchShortSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = Branch
        fields = ('id', 'name', 'code', 'city', 'city_name')
        read_only_fields = fields


class BranchSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = Branch
        fields = (
            'id',
            'city',
            'city_name',
            'name',
            'code',
            'address',
            'phone',
            'email',
            'is_main',
            'opening_time',
            'closing_time',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
