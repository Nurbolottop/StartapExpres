from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm

from apps.users.models import ClientProfile, DeviceSession, DriverProfile, EmployeeProfile, User


class UserCreationForm(DjangoUserCreationForm):
    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ('phone',)


class UserChangeForm(DjangoUserChangeForm):
    class Meta(DjangoUserChangeForm.Meta):
        model = User
        fields = '__all__'


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    ordering = ('-created_at',)
    list_display = ('phone', 'full_name', 'role', 'is_active', 'is_verified')
    list_filter = ('role', 'is_active', 'is_verified')
    search_fields = ('phone', 'last_name', 'first_name', 'email', 'username')
    readonly_fields = ('id', 'last_login', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        (
            'Личные данные',
            {
                'fields': (
                    'last_name',
                    'first_name',
                    'middle_name',
                    'email',
                    'username',
                    'avatar',
                    'language',
                    'timezone',
                )
            },
        ),
        (
            'Доступ',
            {
                'fields': (
                    'role',
                    'is_active',
                    'is_verified',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                )
            },
        ),
        ('Служебные', {'fields': ('id', 'last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('phone', 'password1', 'password2', 'role')}),)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ('client_code', 'user', 'company_name', 'discount_percent', 'balance')
    search_fields = ('client_code', 'user__phone', 'company_name')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(EmployeeProfile)
class EmployeeProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_code', 'user', 'branch', 'position', 'status')
    list_filter = ('status', 'branch')
    search_fields = ('employee_code', 'user__phone')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'driver_license', 'license_expiry_date', 'rating', 'status')
    list_filter = ('status',)
    search_fields = ('user__phone', 'driver_license')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DeviceSession)
class DeviceSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip', 'login_at', 'last_activity', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('user__phone', 'ip')
    readonly_fields = (
        'id',
        'user',
        'refresh_jti',
        'ip',
        'user_agent',
        'login_at',
        'last_activity',
        'created_at',
        'updated_at',
    )
