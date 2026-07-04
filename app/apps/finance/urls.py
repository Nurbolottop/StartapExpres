from rest_framework.routers import DefaultRouter

from apps.finance import views

router = DefaultRouter()
router.register('payments', views.PaymentViewSet, basename='payments')
router.register('invoices', views.InvoiceViewSet, basename='invoices')
router.register('cashboxes', views.CashboxViewSet, basename='cashboxes')
router.register('debts', views.DebtViewSet, basename='debts')
router.register('financial-reports', views.FinancialReportViewSet, basename='financial-reports')

urlpatterns = router.urls
