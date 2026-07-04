from rest_framework.routers import DefaultRouter

from apps.vehicles.views import VehicleTypeViewSet, VehicleViewSet

router = DefaultRouter()
router.register('vehicle-types', VehicleTypeViewSet, basename='vehicle-types')
router.register('vehicles', VehicleViewSet, basename='vehicles')

urlpatterns = router.urls
