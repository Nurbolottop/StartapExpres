from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts import selectors, services
from apps.accounts.constants import Roles
from apps.accounts.filters import UserFilter
from apps.accounts.serializers import (
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    ProfileUpdateSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from apps.common.permissions import role_required


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'


class LogoutView(APIView):
    @extend_schema(request=LogoutSerializer, responses={204: None}, summary='Выход (blacklist refresh-токена)')
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    @extend_schema(responses=UserSerializer, summary='Профиль текущего пользователя')
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=ProfileUpdateSerializer, responses=UserSerializer, summary='Обновление своего профиля')
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_update(user=request.user, data=serializer.validated_data)
        return Response(UserSerializer(user).data)


class PasswordChangeView(APIView):
    @extend_schema(request=PasswordChangeSerializer, responses={204: None}, summary='Смена своего пароля')
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.user_change_password(user=request.user, **serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses=UserSerializer)
class UserViewSet(ModelViewSet):
    """Управление пользователями. Доступно только ADMIN и MANAGER."""

    serializer_class = UserSerializer
    permission_classes = (role_required(Roles.ADMIN, Roles.MANAGER),)
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')

    filterset_class = UserFilter
    search_fields = ('phone', 'last_name', 'first_name', 'email')
    ordering_fields = ('created_at', 'last_name', 'role')

    def get_queryset(self):
        return selectors.user_list()

    @extend_schema(request=UserCreateSerializer, responses={201: UserSerializer}, summary='Создание пользователя')
    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_create(**serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=UserUpdateSerializer, responses=UserSerializer, summary='Изменение пользователя')
    def partial_update(self, request, *args, **kwargs):
        serializer = UserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.user_update(user=self.get_object(), data=serializer.validated_data)
        return Response(UserSerializer(user).data)

    @extend_schema(responses={204: None}, summary='Деактивация пользователя (soft)')
    def destroy(self, request, *args, **kwargs):
        services.user_deactivate(user=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)
