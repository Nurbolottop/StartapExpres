from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.gps import views

router = DefaultRouter()
router.register('geofences', views.GeofenceViewSet, basename='geofences')

urlpatterns = [
    path('gps/update/', views.GPSUpdateView.as_view(), name='gps-update'),
    path('gps/live/', views.GPSLiveView.as_view(), name='gps-live'),
    path('gps/history/', views.GPSHistoryView.as_view(), name='gps-history'),
    path('gps/events/', views.GPSEventListView.as_view(), name='gps-events'),
    *router.urls,
]
