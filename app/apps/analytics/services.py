"""Аналитика и дашборды (ТЗ, разделы 12, 18): только чтение, кэш 30 секунд."""

from django.core.cache import cache
from django.db.models import Avg, Count, Q, Sum
from django.utils import timezone

from apps.finance.choices import DebtStatus, TransactionType
from apps.finance.models import Debt, Payment, Transaction
from apps.orders.choices import OrderStatus
from apps.orders.models import Order
from apps.packages.choices import PackageStatus
from apps.packages.models import Package
from apps.shipments.choices import ACTIVE_STATUSES, ShipmentStatus
from apps.shipments.models import Incident, Shipment
from apps.users.choices import DriverStatus, Roles
from apps.users.models import User
from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle
from apps.warehouses.models import WarehouseCell

DASHBOARD_CACHE_SECONDS = 30

PROBLEM_STATUSES = (OrderStatus.DAMAGED, OrderStatus.LOST, OrderStatus.RETURNED, OrderStatus.NEED_CORRECTION)


class AnalyticsService:
    @staticmethod
    def orders_summary(*, date_from=None, date_to=None) -> dict:
        queryset = Order.objects.all()
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        aggregates = queryset.aggregate(avg_price=Avg('total_price'))
        return {
            'created': queryset.count(),
            'cancelled': queryset.filter(status=OrderStatus.CANCELLED).count(),
            'delivered': queryset.filter(status__in=(OrderStatus.DELIVERED, OrderStatus.COMPLETED)).count(),
            'problem': queryset.filter(status__in=PROBLEM_STATUSES).count(),
            'average_price': str(round(aggregates['avg_price'] or 0, 2)),
        }

    @staticmethod
    def finance_summary(*, date_from=None, date_to=None) -> dict:
        queryset = Transaction.objects.all()
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        income = queryset.filter(type=TransactionType.INCOME).aggregate(s=Sum('amount'))['s'] or 0
        expense = queryset.filter(type=TransactionType.EXPENSE).aggregate(s=Sum('amount'))['s'] or 0
        refunds = queryset.filter(type=TransactionType.REFUND).aggregate(s=Sum('amount'))['s'] or 0
        payments = Payment.objects.aggregate(avg=Avg('amount'), count=Count('id'))
        return {
            'income': str(income),
            'expense': str(abs(expense)),
            'refunds': str(abs(refunds)),
            'profit': str(income + expense + refunds),
            'payments_count': payments['count'],
            'average_check': str(round(payments['avg'] or 0, 2)),
            'open_debts': str(
                Debt.objects.exclude(status=DebtStatus.CLOSED).aggregate(s=Sum('amount'))['s'] or 0
            ),
        }

    @staticmethod
    def warehouse_summary() -> dict:
        cells = WarehouseCell.objects.aggregate(
            total=Count('id'),
            occupied=Count('id', filter=~Q(occupied_weight=0)),
        )
        return {
            'cells_total': cells['total'],
            'cells_occupied': cells['occupied'],
            'cells_free': cells['total'] - cells['occupied'],
            'packages_stored': Package.objects.filter(status=PackageStatus.STORED).count(),
            'packages_damaged': Package.objects.filter(status=PackageStatus.DAMAGED).count(),
            'packages_returned': Package.objects.filter(status=PackageStatus.RETURNED).count(),
        }

    @staticmethod
    def drivers_summary() -> dict:
        return {
            'drivers_total': User.objects.filter(role=Roles.DRIVER, is_active=True).count(),
            'drivers_on_trip': User.objects.filter(
                role=Roles.DRIVER, driver_profile__status=DriverStatus.ON_TRIP
            ).count(),
            'shipments_active': Shipment.objects.filter(status__in=ACTIVE_STATUSES).count(),
            'shipments_completed': Shipment.objects.filter(status=ShipmentStatus.COMPLETED).count(),
            'incidents_total': Incident.objects.count(),
        }


class DashboardService:
    """Ролевые дашборды (ТЗ, раздел 18). Кэш 30 секунд."""

    @classmethod
    def for_user(cls, user) -> dict:
        cache_key = f'dashboard:{user.role}'
        cached = cache.get(cache_key)
        if cached is not None and user.role != Roles.CLIENT:
            return cached
        builder = {
            Roles.SUPERADMIN: cls._management,
            Roles.DIRECTOR: cls._management,
            Roles.FINANCE: cls._finance,
            Roles.OPERATOR: cls._operator,
            Roles.WAREHOUSE: cls._warehouse,
            Roles.DRIVER: cls._driver,
            Roles.CLIENT: cls._client,
        }[user.role]
        data = builder(user)
        if user.role != Roles.CLIENT:
            cache.set(cache_key, data, timeout=DASHBOARD_CACHE_SECONDS)
        return data

    @staticmethod
    def _management(user) -> dict:
        today = timezone.localdate()
        return {
            'users_total': User.objects.count(),
            'clients_total': User.objects.filter(role=Roles.CLIENT).count(),
            'employees_total': User.objects.exclude(role=Roles.CLIENT).count(),
            'vehicles_total': Vehicle.objects.count(),
            'vehicles_available': Vehicle.objects.filter(status=VehicleStatus.AVAILABLE).count(),
            'orders_today': Order.objects.filter(created_at__date=today).count(),
            'active_shipments': Shipment.objects.filter(status__in=ACTIVE_STATUSES).count(),
            'problem_orders': Order.objects.filter(status__in=PROBLEM_STATUSES).count(),
            **AnalyticsService.finance_summary(date_from=today, date_to=today),
        }

    @staticmethod
    def _finance(user) -> dict:
        today = timezone.localdate()
        return AnalyticsService.finance_summary(date_from=today, date_to=today)

    @staticmethod
    def _operator(user) -> dict:
        return {
            'new_orders': Order.objects.filter(status=OrderStatus.WAITING_CONFIRMATION).count(),
            'waiting_payment': Order.objects.filter(
                status__in=(OrderStatus.WAITING_PAYMENT, OrderStatus.PARTIALLY_PAID)
            ).count(),
            'waiting_shipment': Order.objects.filter(status=OrderStatus.WAITING_SHIPMENT).count(),
            'active_shipments': Shipment.objects.filter(status__in=ACTIVE_STATUSES).count(),
            'problem_orders': Order.objects.filter(status__in=PROBLEM_STATUSES).count(),
        }

    @staticmethod
    def _warehouse(user) -> dict:
        return {
            'waiting_receive': Order.objects.filter(status=OrderStatus.WAITING_RECEIVE).count(),
            'waiting_store': Package.objects.filter(
                status__in=(PackageStatus.RECEIVED, PackageStatus.CHECKED)
            ).count(),
            'waiting_loading': Package.objects.filter(status=PackageStatus.WAITING_LOADING).count(),
            'ready_for_pickup': Order.objects.filter(status=OrderStatus.READY_FOR_PICKUP).count(),
            **AnalyticsService.warehouse_summary(),
        }

    @staticmethod
    def _driver(user) -> dict:
        my_active = Shipment.objects.filter(driver=user, status__in=ACTIVE_STATUSES)
        return {
            'my_active_shipments': my_active.count(),
            'my_orders': Order.objects.filter(shipment_items__shipment__in=my_active).distinct().count(),
            'my_completed_shipments': Shipment.objects.filter(
                driver=user, status=ShipmentStatus.COMPLETED
            ).count(),
        }

    @staticmethod
    def _client(user) -> dict:
        my_orders = Order.objects.filter(client=user)
        return {
            'my_orders': my_orders.count(),
            'active_deliveries': my_orders.exclude(
                status__in=(OrderStatus.COMPLETED, OrderStatus.CANCELLED)
            ).count(),
            'completed': my_orders.filter(status=OrderStatus.COMPLETED).count(),
        }
