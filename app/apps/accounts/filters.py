import django_filters

from apps.accounts.models import User


class UserFilter(django_filters.FilterSet):
    class Meta:
        model = User
        fields = ('role', 'branch', 'is_active')
