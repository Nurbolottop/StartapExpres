from django.urls import path

from apps.common import views

urlpatterns = [
    path('health/', views.HealthView.as_view(), name='health'),
    path('health/db/', views.DatabaseHealthView.as_view(), name='health-db'),
    path('health/cache/', views.CacheHealthView.as_view(), name='health-cache'),
    path('health/redis/', views.RedisHealthView.as_view(), name='health-redis'),
    path('health/celery/', views.CeleryHealthView.as_view(), name='health-celery'),
    path('health/storage/', views.StorageHealthView.as_view(), name='health-storage'),
]
