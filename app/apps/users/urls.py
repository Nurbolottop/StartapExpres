from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.users import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='users')
router.register('clients', views.ClientViewSet, basename='clients')

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', views.RefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('auth/logout-all/', views.LogoutAllView.as_view(), name='auth-logout-all'),
    path('auth/me/', views.MeView.as_view(), name='auth-me'),
    path('auth/change-password/', views.PasswordChangeView.as_view(), name='auth-change-password'),
    path('auth/sessions/', views.SessionListView.as_view(), name='auth-sessions'),
    path(
        'auth/sessions/<uuid:session_id>/',
        views.SessionTerminateView.as_view(),
        name='auth-session-terminate',
    ),
    *router.urls,
]
