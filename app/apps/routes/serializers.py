from rest_framework import serializers

from apps.routes.models import Route, RoutePoint


class RoutePointSerializer(serializers.ModelSerializer):
    city_name = serializers.CharField(source='city.name', read_only=True)

    class Meta:
        model = RoutePoint
        fields = (
            'id',
            'route',
            'city',
            'city_name',
            'sequence',
            'latitude',
            'longitude',
            'is_active',
            'created_at',
        )
        read_only_fields = ('id', 'created_at')


class RouteSerializer(serializers.ModelSerializer):
    start_branch_name = serializers.CharField(source='start_branch.name', read_only=True)
    end_branch_name = serializers.CharField(source='end_branch.name', read_only=True)
    points = RoutePointSerializer(many=True, read_only=True)

    class Meta:
        model = Route
        fields = (
            'id',
            'name',
            'code',
            'start_branch',
            'start_branch_name',
            'end_branch',
            'end_branch_name',
            'estimated_distance',
            'estimated_duration',
            'points',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
