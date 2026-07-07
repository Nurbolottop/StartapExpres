from rest_framework import serializers

from apps.users.choices import Languages, Roles
from apps.users.models import ClientProfile, DeviceSession, DriverProfile, EmployeeProfile, User


class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = (
            'client_code',
            'company_name',
            'passport_number',
            'address',
            'notes',
            'discount_percent',
            'balance',
        )
        read_only_fields = ('client_code', 'balance')


class EmployeeProfileSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.name', read_only=True)

    class Meta:
        model = EmployeeProfile
        fields = (
            'employee_code',
            'branch',
            'branch_name',
            'department',
            'position',
            'hired_at',
            'salary',
            'status',
        )
        read_only_fields = ('employee_code',)


class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = (
            'driver_license',
            'license_expiry_date',
            'medical_certificate',
            'experience_years',
            'rating',
            'status',
        )
        read_only_fields = ('rating',)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'phone',
            'email',
            'username',
            'last_name',
            'first_name',
            'middle_name',
            'full_name',
            'role',
            'avatar',
            'language',
            'timezone',
            'is_verified',
            'is_active',
            'last_login',
            'created_at',
            'profile',
        )
        read_only_fields = fields

    def get_profile(self, user: User) -> dict | None:
        if user.role == Roles.CLIENT and hasattr(user, 'client_profile'):
            return ClientProfileSerializer(user.client_profile).data
        if user.role == Roles.DRIVER and hasattr(user, 'driver_profile'):
            return DriverProfileSerializer(user.driver_profile).data
        if hasattr(user, 'employee_profile'):
            return EmployeeProfileSerializer(user.employee_profile).data
        return None


class RegisterSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    first_name = serializers.CharField(max_length=150, required=False, default='')
    last_name = serializers.CharField(max_length=150, required=False, default='')


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = UserSerializer(read_only=True)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class PhoneSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class PhoneVerifyConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=16)
    code = serializers.CharField(max_length=6)


class ProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    language = serializers.ChoiceField(choices=Languages.choices, required=False)
    timezone = serializers.CharField(max_length=64, required=False)


class DeviceSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceSession
        fields = ('id', 'ip', 'user_agent', 'login_at', 'last_activity', 'is_active')
        read_only_fields = fields


class UserWriteSerializer(serializers.Serializer):
    """Общие поля создания/изменения пользователя сотрудниками."""

    phone = serializers.CharField(max_length=16, required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    middle_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=Roles.choices, required=False)
    language = serializers.ChoiceField(choices=Languages.choices, required=False)
    timezone = serializers.CharField(max_length=64, required=False)
    is_active = serializers.BooleanField(required=False)
    is_verified = serializers.BooleanField(required=False)
    # Профильные поля (применяются к профилю согласно роли)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    passport_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address = serializers.CharField(max_length=255, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    branch = serializers.UUIDField(required=False, allow_null=True)
    department = serializers.CharField(max_length=150, required=False, allow_blank=True)
    position = serializers.CharField(max_length=150, required=False, allow_blank=True)
    hired_at = serializers.DateField(required=False, allow_null=True)
    salary = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    driver_license = serializers.CharField(max_length=50, required=False, allow_blank=True)
    license_expiry_date = serializers.DateField(required=False, allow_null=True)
    medical_certificate = serializers.CharField(max_length=100, required=False, allow_blank=True)
    experience_years = serializers.IntegerField(min_value=0, required=False)

    def validate_branch(self, value):
        if value is None:
            return None
        from apps.branches.models import Branch

        branch = Branch.objects.filter(id=value).first()
        if branch is None:
            raise serializers.ValidationError('Филиал не найден.')
        return branch


class UserCreateSerializer(UserWriteSerializer):
    phone = serializers.CharField(max_length=16)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    role = serializers.ChoiceField(choices=Roles.choices)
