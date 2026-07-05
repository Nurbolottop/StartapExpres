from rest_framework.routers import DefaultRouter

from apps.notifications.views import NotificationTemplateViewSet, NotificationViewSet

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notifications')
router.register('notification-templates', NotificationTemplateViewSet, basename='notification-templates')

urlpatterns = router.urls
