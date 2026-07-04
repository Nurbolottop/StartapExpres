import django_filters

from apps.users.models import User


class UserFilter(django_filters.FilterSet):
    branch = django_filters.UUIDFilter(field_name='employee_profile__branch_id')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = User
        fields = ('role', 'is_active', 'is_verified')
