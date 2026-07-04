from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.tariffs.views import AdditionalServiceViewSet, TariffCalculateView, TariffViewSet

router = DefaultRouter()
router.register('tariffs', TariffViewSet, basename='tariffs')
router.register('additional-services', AdditionalServiceViewSet, basename='additional-services')

urlpatterns = [
    path('tariffs/calculate/', TariffCalculateView.as_view(), name='tariffs-calculate'),
    *router.urls,
]
