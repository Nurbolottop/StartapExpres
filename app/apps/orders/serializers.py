from decimal import Decimal

from rest_framework import serializers

from apps.branches.models import Branch
from apps.orders.choices import DeliveryType, OrderStatus, PaymentType
from apps.orders.models import Order, OrderStatusHistory
from apps.packages.serializers import PackageSerializer, PackageWriteSerializer
from apps.tariffs.models import AdditionalService


class OrderServiceItemField(serializers.Serializer):
    code = serializers.CharField(source='service.code', read_only=True)
    name = serializers.CharField(source='service.name', read_only=True)
    price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    client_phone = serializers.CharField(source='client.phone', read_only=True)
    from_branch_name = serializers.CharField(source='from_branch.name', read_only=True)
    to_branch_name = serializers.CharField(source='to_branch.name', read_only=True)
    packages = PackageSerializer(many=True, read_only=True)
    services = OrderServiceItemField(source='service_items', many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'order_number',
            'client',
            'client_phone',
            'sender_name',
            'sender_phone',
            'sender_address',
            'receiver_name',
            'receiver_phone',
            'receiver_address',
            'from_branch',
            'from_branch_name',
            'to_branch',
            'to_branch_name',
            'payment_type',
            'delivery_type',
            'tariff',
            'total_price',
            'insurance_price',
            'paid_amount',
            'price_details',
            'status',
            'comment',
            'version',
            'packages',
            'services',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class OrderCreateSerializer(serializers.Serializer):
    client = serializers.UUIDField(required=False, allow_null=True, default=None)
    sender_name = serializers.CharField(max_length=255)
    sender_phone = serializers.CharField(max_length=16)
    sender_address = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    receiver_name = serializers.CharField(max_length=255)
    receiver_phone = serializers.CharField(max_length=16)
    receiver_address = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')
    from_branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    to_branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all())
    payment_type = serializers.ChoiceField(choices=PaymentType.choices, default=PaymentType.CASH)
    delivery_type = serializers.ChoiceField(choices=DeliveryType.choices, default=DeliveryType.BRANCH_PICKUP)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
    packages = PackageWriteSerializer(many=True)
    services = serializers.PrimaryKeyRelatedField(
        queryset=AdditionalService.objects.filter(is_active=True),
        many=True,
        required=False,
        default=list,
    )

    def validate_packages(self, value):
        if not value:
            raise serializers.ValidationError('Нужно хотя бы одно грузовое место.')
        return value

    def validate_client(self, value):
        if value is None:
            return None
        from apps.users.choices import Roles
        from apps.users.models import User

        client = User.objects.filter(id=value, role=Roles.CLIENT).first()
        if client is None:
            raise serializers.ValidationError('Клиент не найден.')
        return client


class OrderUpdateSerializer(serializers.Serializer):
    sender_name = serializers.CharField(max_length=255, required=False)
    sender_phone = serializers.CharField(max_length=16, required=False)
    sender_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    receiver_name = serializers.CharField(max_length=255, required=False)
    receiver_phone = serializers.CharField(max_length=16, required=False)
    receiver_address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    from_branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    to_branch = serializers.PrimaryKeyRelatedField(queryset=Branch.objects.all(), required=False)
    payment_type = serializers.ChoiceField(choices=PaymentType.choices, required=False)
    delivery_type = serializers.ChoiceField(choices=DeliveryType.choices, required=False)
    comment = serializers.CharField(required=False, allow_blank=True)


class OrderStatusChangeSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OrderStatus.choices)
    comment = serializers.CharField(required=False, allow_blank=True, default='')
    version = serializers.IntegerField(required=False, allow_null=True, default=None)


class OrderCancelSerializer(serializers.Serializer):
    comment = serializers.CharField(required=False, allow_blank=True, default='')


class OrderCorrectionSerializer(serializers.Serializer):
    comment = serializers.CharField()


class OrderPaySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.01'))


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True, default=None)

    class Meta:
        model = OrderStatusHistory
        fields = ('id', 'from_status', 'to_status', 'changed_by', 'changed_by_name', 'comment', 'created_at')
        read_only_fields = fields
