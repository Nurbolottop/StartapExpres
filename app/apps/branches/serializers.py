from rest_framework import serializers

from apps.branches.models import Branch


class BranchShortSerializer(serializers.ModelSerializer):
    """Компактное представление филиала для вложенных объектов."""

    class Meta:
        model = Branch
        fields = ('id', 'name', 'code', 'city')
        read_only_fields = fields


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = (
            'id',
            'name',
            'code',
            'city',
            'address',
            'phone',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
