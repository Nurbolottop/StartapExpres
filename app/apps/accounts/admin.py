from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm as DjangoUserChangeForm
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm

from apps.accounts.models import User


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
    list_display = ('phone', 'full_name', 'role', 'branch', 'is_active')
    list_filter = ('role', 'is_active', 'branch')
    search_fields = ('phone', 'last_name', 'first_name', 'email')
    readonly_fields = ('id', 'last_login', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Личные данные', {'fields': ('last_name', 'first_name', 'middle_name', 'email')}),
        ('Доступ', {'fields': ('role', 'branch', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Служебные', {'fields': ('id', 'last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('phone', 'password1', 'password2', 'role', 'branch')}),
    )
