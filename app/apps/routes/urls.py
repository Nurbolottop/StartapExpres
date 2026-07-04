from rest_framework.routers import DefaultRouter

from apps.routes.views import RoutePointViewSet, RouteViewSet

router = DefaultRouter()
router.register('routes', RouteViewSet, basename='routes')
router.register('route-points', RoutePointViewSet, basename='route-points')

urlpatterns = router.urls
