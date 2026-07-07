from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.notifications.views import (
    DeviceRegisterView,
    DeviceUnregisterView,
    NotificationTemplateViewSet,
    NotificationViewSet,
)

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notifications')
router.register('notification-templates', NotificationTemplateViewSet, basename='notification-templates')

urlpatterns = [
    path('auth/devices/', DeviceRegisterView.as_view(), name='auth-devices'),
    path('auth/devices/<str:device_id>/', DeviceUnregisterView.as_view(), name='auth-device-unregister'),
    *router.urls,
]
