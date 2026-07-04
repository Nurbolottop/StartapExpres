from rest_framework.routers import DefaultRouter

from apps.shipments.views import ShipmentViewSet

router = DefaultRouter()
router.register('shipments', ShipmentViewSet, basename='shipments')

urlpatterns = router.urls
