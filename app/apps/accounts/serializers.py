from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.constants import Roles
from apps.accounts.models import User
from apps.branches.models import Branch
from apps.branches.serializers import BranchShortSerializer
from apps.common.exceptions import ApplicationError


class UserSerializer(serializers.ModelSerializer):
    branch = BranchShortSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'phone',
            'email',
            'last_name',
            'first_name',
            'middle_name',
            'full_name',
            'role',
            'branch',
            'is_active',
            'last_login',
            'created_at',
        )
        read_only_fields = fields


class UserCreateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=Roles.choices)
    last_name = serializers.CharField(max_length=150, required=False, default='')
    first_name = serializers.CharField(max_length=150, required=False, default='')
    middle_name = serializers.CharField(max_length=150, required=False, default='')
    email = serializers.EmailField(required=False, default='')
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False, allow_null=True, default=None
    )


class UserUpdateSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16, required=False)
    role = serializers.ChoiceField(choices=Roles.choices, required=False)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(), required=False, allow_null=True
    )
    is_active = serializers.BooleanField(required=False)


class ProfileUpdateSerializer(serializers.Serializer):
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class LoginSerializer(TokenObtainPairSerializer):
    """Стандартный obtain-pair + данные пользователя в ответе."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def save(self, **kwargs):
        try:
            RefreshToken(self.validated_data['refresh']).blacklist()
        except TokenError:
            raise ApplicationError('Недействительный refresh-токен.', code='invalid_token')
