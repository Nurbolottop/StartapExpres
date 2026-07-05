from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import AnalyticsService, DashboardService
from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewAnalytics(RolePermission):
    """Аналитика — руководство и финансы (ТЗ, раздел 14)."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.FINANCE)


@extend_schema(tags=['dashboard'])
class DashboardView(APIView):
    """Ролевой дашборд (ТЗ, раздел 18): каждая роль видит свои показатели."""

    permission_classes = (IsAuthenticated,)

    @extend_schema(responses={200: dict}, summary='Дашборд по роли')
    def get(self, request):
        return Response(DashboardService.for_user(request.user))


class _ReportView(APIView):
    permission_classes = (CanViewAnalytics,)
    summary_method = ''

    @extend_schema(responses={200: dict}, tags=['reports'])
    def get(self, request):
        method = getattr(AnalyticsService, self.summary_method)
        kwargs = {}
        if self.summary_method in ('orders_summary', 'finance_summary'):
            kwargs = {
                'date_from': request.query_params.get('date_from'),
                'date_to': request.query_params.get('date_to'),
            }
        return Response(method(**kwargs))


class OrdersReportView(_ReportView):
    summary_method = 'orders_summary'


class FinanceReportView(_ReportView):
    summary_method = 'finance_summary'


class WarehouseReportView(_ReportView):
    summary_method = 'warehouse_summary'


class DriversReportView(_ReportView):
    summary_method = 'drivers_summary'
