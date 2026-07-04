from rest_framework.routers import DefaultRouter

from apps.branches.views import BranchViewSet, CityViewSet

router = DefaultRouter()
router.register('cities', CityViewSet, basename='cities')
router.register('branches', BranchViewSet, basename='branches')

urlpatterns = router.urls
