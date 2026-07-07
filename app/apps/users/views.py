from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenRefreshView

from apps.common.permissions import ActionPermissionsMixin
from apps.users import permissions as users_permissions
from apps.users.choices import Roles
from apps.users.filters import UserFilter
from apps.users.selectors import UserSelector
from apps.users.serializers import (
    DeviceSessionSerializer,
    LoginSerializer,
    LogoutSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PhoneSerializer,
    PhoneVerifyConfirmSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    TokenPairSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserWriteSerializer,
)
from apps.users.services import AuthService, UserService


class RegisterView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'

    @extend_schema(
        request=RegisterSerializer,
        responses={201: TokenPairSerializer},
        summary='Регистрация клиента',
        tags=['auth'],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthService.register(**serializer.validated_data)
        return Response(TokenPairSerializer(result).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'

    @extend_schema(
        request=LoginSerializer,
        responses=TokenPairSerializer,
        summary='Вход по телефону и паролю',
        tags=['auth'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthService.login(**serializer.validated_data)
        return Response(TokenPairSerializer(result).data)


class RefreshView(TokenRefreshView):
    """Обновление access-токена (simplejwt, rotation + blacklist)."""

    def post(self, request, *args, **kwargs):
        old_refresh = request.data.get('refresh', '')
        response = super().post(request, *args, **kwargs)
        new_refresh = response.data.get('refresh') if isinstance(response.data, dict) else None
        if new_refresh:
            AuthService.rotate_session(old_refresh=old_refresh, new_refresh=new_refresh)
        return response


class LogoutView(APIView):
    @extend_schema(
        request=LogoutSerializer,
        responses={204: None},
        summary='Выход (blacklist refresh-токена)',
        tags=['auth'],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.logout(user=request.user, refresh_token=serializer.validated_data['refresh'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllView(APIView):
    @extend_schema(request=None, responses={204: None}, summary='Выход со всех устройств', tags=['auth'])
    def post(self, request):
        AuthService.logout_all(user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    @extend_schema(responses=UserSerializer, summary='Мой профиль', tags=['auth'])
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(
        request=ProfileUpdateSerializer,
        responses=UserSerializer,
        summary='Обновление своего профиля',
        tags=['auth'],
    )
    def patch(self, request):
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_self(user=request.user, data=serializer.validated_data)
        return Response(UserSerializer(user).data)


class PasswordChangeView(APIView):
    @extend_schema(
        request=PasswordChangeSerializer, responses={204: None}, summary='Смена своего пароля', tags=['auth']
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.change_password(user=request.user, **serializer.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'

    @extend_schema(
        request=PhoneSerializer,
        responses={200: None},
        summary='Восстановление пароля: запрос SMS-кода',
        description='Ответ всегда успешный — существование номера не раскрывается. '
        'Код живёт 10 минут, повторный запрос — не чаще раза в минуту (429 AUTH_008).',
        tags=['auth'],
    )
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.password_reset_request(**serializer.validated_data)
        return Response({'sent': True})


class PasswordResetConfirmView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: None},
        summary='Восстановление пароля: установка нового по SMS-коду',
        description='Неверный/истёкший код — 400 AUTH_007 (максимум 5 попыток). '
        'После смены пароля все сессии и refresh-токены отзываются.',
        tags=['auth'],
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.password_reset_confirm(**serializer.validated_data)
        return Response({'reset': True})


class PhoneVerifyRequestView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'

    @extend_schema(
        request=PhoneSerializer,
        responses={200: None},
        summary='Верификация телефона: запрос SMS-кода',
        description='Ответ всегда успешный. Для уже подтверждённого номера SMS не шлётся.',
        tags=['auth'],
    )
    def post(self, request):
        serializer = PhoneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        AuthService.verify_request(**serializer.validated_data)
        return Response({'sent': True})


class PhoneVerifyConfirmView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'auth'

    @extend_schema(
        request=PhoneVerifyConfirmSerializer,
        responses=UserSerializer,
        summary='Верификация телефона: подтверждение кода',
        description='Успех — is_verified=true. Неверный/истёкший код — 400 AUTH_007.',
        tags=['auth'],
    )
    def post(self, request):
        serializer = PhoneVerifyConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.verify_confirm(**serializer.validated_data)
        return Response(UserSerializer(user).data)


class SessionListView(APIView):
    @extend_schema(responses=DeviceSessionSerializer(many=True), summary='Мои активные сессии', tags=['auth'])
    def get(self, request):
        sessions = UserSelector.active_sessions(request.user)
        return Response(DeviceSessionSerializer(sessions, many=True).data)


class SessionTerminateView(APIView):
    @extend_schema(responses={204: None}, summary='Завершить сессию устройства', tags=['auth'])
    def delete(self, request, session_id):
        AuthService.terminate_session(user=request.user, session_id=session_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['users'])
class UserViewSet(ActionPermissionsMixin, ModelViewSet):
    """Управление пользователями (матрица прав — ТЗ, раздел 14)."""

    serializer_class = UserSerializer
    http_method_names = ('get', 'post', 'patch', 'delete', 'head', 'options')
    filterset_class = UserFilter
    search_fields = ('phone', 'last_name', 'first_name', 'email', 'username')
    ordering_fields = ('created_at', 'last_name', 'role')

    permission_classes_by_action = {
        '__default__': (users_permissions.CanViewUsers,),
        'create': (users_permissions.CanManageUsers,),
        'partial_update': (users_permissions.CanManageUsers,),
        'destroy': (users_permissions.CanDeleteUsers,),
    }

    def get_queryset(self):
        return UserSelector.list()

    @extend_schema(
        request=UserCreateSerializer, responses={201: UserSerializer}, summary='Создание пользователя'
    )
    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.create(actor=request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=UserWriteSerializer, responses=UserSerializer, summary='Изменение пользователя')
    def partial_update(self, request, *args, **kwargs):
        serializer = UserWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update(actor=request.user, user=self.get_object(), data=serializer.validated_data)
        return Response(UserSerializer(user).data)

    @extend_schema(responses={204: None}, summary='Удаление пользователя (soft delete)')
    def destroy(self, request, *args, **kwargs):
        UserService.soft_delete(actor=request.user, user=self.get_object())
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=['clients'])
class ClientViewSet(ActionPermissionsMixin, ModelViewSet):
    """Работа операторов с клиентами (ТЗ, раздел 03: /clients)."""

    serializer_class = UserSerializer
    http_method_names = ('get', 'post', 'patch', 'head', 'options')
    search_fields = (
        'phone',
        'last_name',
        'first_name',
        'client_profile__company_name',
        'client_profile__client_code',
    )
    ordering_fields = ('created_at', 'last_name')

    permission_classes_by_action = {
        '__default__': (users_permissions.CanManageClients,),
    }

    def get_queryset(self):
        return UserSelector.clients()

    @extend_schema(request=UserCreateSerializer, responses={201: UserSerializer}, summary='Создание клиента')
    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(data={**request.data, 'role': Roles.CLIENT})
        serializer.is_valid(raise_exception=True)
        user = UserService.create(actor=request.user, **serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=UserWriteSerializer, responses=UserSerializer, summary='Изменение клиента')
    def partial_update(self, request, *args, **kwargs):
        data = {key: value for key, value in request.data.items() if key != 'role'}
        serializer = UserWriteSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update(actor=request.user, user=self.get_object(), data=serializer.validated_data)
        return Response(UserSerializer(user).data)
