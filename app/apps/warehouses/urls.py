from rest_framework.routers import DefaultRouter

from apps.warehouses.views import WarehouseCellViewSet, WarehouseViewSet, WarehouseZoneViewSet

router = DefaultRouter()
router.register('warehouses', WarehouseViewSet, basename='warehouses')
router.register('warehouse-zones', WarehouseZoneViewSet, basename='warehouse-zones')
router.register('warehouse-cells', WarehouseCellViewSet, basename='warehouse-cells')

urlpatterns = router.urls
