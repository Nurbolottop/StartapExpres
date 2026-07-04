from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.warehouses import views_ops
from apps.warehouses.views import WarehouseCellViewSet, WarehouseViewSet, WarehouseZoneViewSet

router = DefaultRouter()
router.register('warehouses', WarehouseViewSet, basename='warehouses')
router.register('warehouse-zones', WarehouseZoneViewSet, basename='warehouse-zones')
router.register('warehouse-cells', WarehouseCellViewSet, basename='warehouse-cells')

urlpatterns = [
    path('warehouse-operations/receive/', views_ops.ReceiveView.as_view(), name='wh-receive'),
    path('warehouse-operations/check/', views_ops.CheckView.as_view(), name='wh-check'),
    path('warehouse-operations/store/', views_ops.StoreView.as_view(), name='wh-store'),
    path('warehouse-operations/move/', views_ops.MoveView.as_view(), name='wh-move'),
    path('warehouse-operations/damage/', views_ops.DamageReportView.as_view(), name='wh-damage'),
    path('warehouse-operations/lost/', views_ops.LostReportView.as_view(), name='wh-lost'),
    path('warehouse-operations/inventory/', views_ops.InventoryOpenView.as_view(), name='wh-inventory-open'),
    path(
        'warehouse-operations/inventory/<uuid:session_id>/scan/',
        views_ops.InventoryScanView.as_view(),
        name='wh-inventory-scan',
    ),
    path(
        'warehouse-operations/inventory/<uuid:session_id>/close/',
        views_ops.InventoryCloseView.as_view(),
        name='wh-inventory-close',
    ),
    path('orders/<uuid:order_id>/issue/', views_ops.OrderIssueView.as_view(), name='order-issue'),
    *router.urls,
]
