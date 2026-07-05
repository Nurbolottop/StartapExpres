from django.urls import path

from apps.analytics import views

urlpatterns = [
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('reports/orders/', views.OrdersReportView.as_view(), name='reports-orders'),
    path('reports/finance/', views.FinanceReportView.as_view(), name='reports-finance'),
    path('reports/warehouse/', views.WarehouseReportView.as_view(), name='reports-warehouse'),
    path('reports/drivers/', views.DriversReportView.as_view(), name='reports-drivers'),
]
