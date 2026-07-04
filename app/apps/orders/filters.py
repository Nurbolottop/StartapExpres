import django_filters

from apps.orders.models import Order


class OrderFilter(django_filters.FilterSet):
    branch = django_filters.UUIDFilter(method='filter_branch')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')

    class Meta:
        model = Order
        fields = ('status', 'client', 'from_branch', 'to_branch', 'payment_type', 'delivery_type')

    def filter_branch(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(Q(from_branch_id=value) | Q(to_branch_id=value))
