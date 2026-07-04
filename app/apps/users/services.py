"""Сервисный слой users: аутентификация, сессии, управление пользователями.

Вся запись — только здесь (ТЗ, разделы 05, 22). Каждая операция публикует
доменное событие; audit пишется подписчиком (ТЗ, раздел 17).
"""

import logging

from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common import events
from apps.common.logging import request_context
from apps.common.services import generate_number
from apps.users import exceptions
from apps.users.choices import Roles
from apps.users.models import ClientProfile, DeviceSession, DriverProfile, EmployeeProfile, User

logger = logging.getLogger(__name__)

BRUTE_FORCE_LIMIT = 5
BRUTE_FORCE_TTL = 30 * 60  # 30 минут блокировки (ТЗ, раздел 30)
BRUTE_FORCE_HARD_LIMIT = 20

_CLIENT_PROFILE_FIELDS = frozenset(
    {'company_name', 'passport_number', 'address', 'notes', 'discount_percent'}
)
_EMPLOYEE_PROFILE_FIELDS = frozenset({'branch', 'department', 'position', 'hired_at', 'salary'})
_DRIVER_PROFILE_FIELDS = frozenset(
    {'driver_license', 'license_expiry_date', 'medical_certificate', 'experience_years'}
)
PROFILE_FIELDS = _CLIENT_PROFILE_FIELDS | _EMPLOYEE_PROFILE_FIELDS | _DRIVER_PROFILE_FIELDS
SELF_EDITABLE_FIELDS = frozenset(
    {'email', 'last_name', 'first_name', 'middle_name', 'language', 'timezone', 'avatar'}
)
USER_FIELDS = frozenset(
    {
        'phone',
        'email',
        'username',
        'last_name',
        'first_name',
        'middle_name',
        'role',
        'language',
        'timezone',
        'avatar',
        'is_active',
        'is_verified',
    }
)


def _attempts_key(phone: str) -> str:
    return f'auth:attempts:{phone}'


def _failures_key(phone: str) -> str:
    return f'auth:failures:{phone}'


def _hard_block_key(phone: str) -> str:
    return f'auth:hard_block:{phone}'


class AuthService:
    """Вход, регистрация, сессии устройств, защита от подбора пароля."""

    @staticmethod
    def _issue_tokens(user: User) -> tuple[str, str, str]:
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token), str(refresh), str(refresh['jti'])

    @staticmethod
    def _create_session(user: User, jti: str) -> DeviceSession:
        context = request_context.get()
        return DeviceSession.objects.create(
            user=user,
            refresh_jti=jti,
            ip=context.get('ip') or None,
            user_agent=context.get('user_agent', ''),
            created_by=user,
        )

    @classmethod
    @transaction.atomic
    def register(cls, *, phone: str, password: str, first_name: str = '', last_name: str = '') -> dict:
        """Публичная регистрация клиента (ТЗ, раздел 03)."""
        user = User(phone=phone, first_name=first_name, last_name=last_name, role=Roles.CLIENT)
        validate_password(password, user)
        user.set_password(password)
        user.full_clean(exclude=['password'])
        user.save()
        UserService.create_profile(user)

        access, refresh, jti = cls._issue_tokens(user)
        cls._create_session(user, jti)
        events.publish(
            'user.registered',
            {
                'actor_id': str(user.id),
                'model': 'User',
                'object_id': str(user.id),
                'action': 'register',
                'new': {'phone': user.phone, 'role': user.role},
            },
            source='users',
        )
        return {'access': access, 'refresh': refresh, 'user': user}

    @classmethod
    def login(cls, *, phone: str, password: str) -> dict:
        cls._check_brute_force(phone)
        user = User.objects.filter(phone=phone).first()

        if user is None or not user.check_password(password):
            cls._register_failure(phone)
            raise exceptions.InvalidCredentialsException()
        if not user.is_active:
            raise exceptions.UserBlockedException()

        cache.delete_many([_attempts_key(phone), _failures_key(phone)])
        access, refresh, jti = cls._issue_tokens(user)
        cls._create_session(user, jti)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        events.publish(
            'user.logged_in',
            {'actor_id': str(user.id), 'model': 'User', 'object_id': str(user.id), 'action': 'login'},
            source='users',
        )
        return {'access': access, 'refresh': refresh, 'user': user}

    @staticmethod
    def _check_brute_force(phone: str) -> None:
        if cache.get(_hard_block_key(phone)):
            raise exceptions.UserBlockedException('Вход заблокирован. Обратитесь к администратору.')
        if cache.get(_attempts_key(phone), 0) >= BRUTE_FORCE_LIMIT:
            raise exceptions.TooManyAttemptsException()

    @staticmethod
    def _register_failure(phone: str) -> None:
        if not cache.add(_attempts_key(phone), 1, timeout=BRUTE_FORCE_TTL):
            cache.incr(_attempts_key(phone))
        if not cache.add(_failures_key(phone), 1, timeout=None):
            cache.incr(_failures_key(phone))
        if cache.get(_failures_key(phone), 0) >= BRUTE_FORCE_HARD_LIMIT:
            cache.set(_hard_block_key(phone), True, timeout=None)
            events.publish(
                'security.login_hard_blocked',
                {'actor_id': None, 'model': 'User', 'object_id': phone, 'action': 'hard_block'},
                source='users',
            )

    @staticmethod
    def rotate_session(*, old_refresh: str, new_refresh: str) -> None:
        """При ротации refresh-токена сессия перепривязывается к новому jti,
        чтобы «завершить сессию» продолжало работать после обновления токена."""
        from rest_framework_simplejwt.state import token_backend

        try:
            old_jti = token_backend.decode(old_refresh, verify=False).get('jti')
            new_jti = token_backend.decode(new_refresh, verify=False).get('jti')
        except Exception:  # noqa: BLE001 — повреждённый токен не должен ломать refresh
            return
        if old_jti and new_jti:
            DeviceSession.objects.filter(refresh_jti=old_jti).update(refresh_jti=new_jti)

    @staticmethod
    def logout(*, user: User, refresh_token: str) -> None:
        try:
            token = RefreshToken(refresh_token)
            jti = str(token['jti'])
            token.blacklist()
        except TokenError as exc:
            raise exceptions.InvalidRefreshTokenException() from exc
        DeviceSession.objects.filter(user=user, refresh_jti=jti).update(is_active=False)
        events.publish(
            'user.logged_out',
            {'actor_id': str(user.id), 'model': 'User', 'object_id': str(user.id), 'action': 'logout'},
            source='users',
        )

    @staticmethod
    def logout_all(*, user: User) -> int:
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        closed = DeviceSession.objects.filter(user=user, is_active=True).update(is_active=False)
        events.publish(
            'user.logged_out_all',
            {
                'actor_id': str(user.id),
                'model': 'User',
                'object_id': str(user.id),
                'action': 'logout_all',
                'new': {'sessions_closed': closed},
            },
            source='users',
        )
        return closed

    @staticmethod
    def terminate_session(*, user: User, session_id) -> None:
        session = DeviceSession.objects.filter(user=user, id=session_id, is_active=True).first()
        if session is None:
            raise exceptions.SessionNotFoundException()
        token = OutstandingToken.objects.filter(user=user, jti=session.refresh_jti).first()
        if token:
            BlacklistedToken.objects.get_or_create(token=token)
        session.is_active = False
        session.save(update_fields=['is_active', 'updated_at'])

    @staticmethod
    def change_password(*, user: User, old_password: str, new_password: str) -> None:
        if not user.check_password(old_password):
            raise exceptions.InvalidCredentialsException('Текущий пароль указан неверно.')
        validate_password(new_password, user)
        user.set_password(new_password)
        user.save(update_fields=['password', 'updated_at'])
        events.publish(
            'user.password_changed',
            {
                'actor_id': str(user.id),
                'model': 'User',
                'object_id': str(user.id),
                'action': 'change_password',
            },
            source='users',
        )


class UserService:
    """Управление пользователями и профилями (ТЗ, разделы 02, 14, 20, 22)."""

    @staticmethod
    def create_profile(user: User) -> None:
        if user.role == Roles.CLIENT:
            ClientProfile.objects.get_or_create(
                user=user,
                defaults={'client_code': generate_number('CLT', yearly=False)},
            )
        elif user.role == Roles.DRIVER:
            DriverProfile.objects.get_or_create(user=user)
        else:
            EmployeeProfile.objects.get_or_create(
                user=user,
                defaults={'employee_code': generate_number('EMP', yearly=False)},
            )

    @classmethod
    @transaction.atomic
    def create(cls, *, actor: User, phone: str, password: str, role: str, **fields) -> User:
        cls._check_role_assignment(actor, role)
        profile_data = {key: fields.pop(key) for key in list(fields) if key in PROFILE_FIELDS}

        user = User(phone=phone, role=role, created_by=actor, **fields)
        validate_password(password, user)
        user.set_password(password)
        user.full_clean(exclude=['password'])
        user.save()
        cls.create_profile(user)
        cls._apply_profile_data(user, profile_data)

        events.publish(
            'user.created',
            {
                'actor_id': str(actor.id),
                'model': 'User',
                'object_id': str(user.id),
                'action': 'create',
                'new': {'phone': user.phone, 'role': user.role},
            },
            source='users',
        )
        return user

    @classmethod
    @transaction.atomic
    def update(cls, *, actor: User, user: User, data: dict) -> User:
        new_role = data.get('role')
        role_changed = bool(new_role) and new_role != user.role
        if role_changed:
            cls._check_role_assignment(actor, new_role)
            cls._ensure_not_last_superadmin(user)
        if data.get('is_active') is False:
            cls._ensure_not_self(actor, user)
            cls._ensure_not_last_superadmin(user)

        profile_data = {key: data.pop(key) for key in list(data) if key in PROFILE_FIELDS}
        unknown = set(data) - USER_FIELDS
        if unknown:
            raise exceptions.RoleNotAllowedException(
                f'Поля недоступны для изменения: {", ".join(sorted(unknown))}.'
            )

        old = {field: str(getattr(user, field)) for field in data}
        for field, value in data.items():
            setattr(user, field, value)
        user.updated_by = actor
        user.full_clean(exclude=['password'])
        user.save()
        if role_changed:
            cls.create_profile(user)
        cls._apply_profile_data(user, profile_data)

        events.publish(
            'user.updated',
            {
                'actor_id': str(actor.id),
                'model': 'User',
                'object_id': str(user.id),
                'action': 'update',
                'old': old,
                'new': {field: str(getattr(user, field)) for field in old},
            },
            source='users',
        )
        return user

    @classmethod
    @transaction.atomic
    def soft_delete(cls, *, actor: User, user: User) -> None:
        cls._ensure_not_self(actor, user)
        cls._ensure_not_last_superadmin(user)
        user.is_active = False
        user.updated_by = actor
        user.save(update_fields=['is_active', 'updated_by', 'updated_at'])
        user.delete()
        AuthService.logout_all(user=user)
        events.publish(
            'user.deleted',
            {'actor_id': str(actor.id), 'model': 'User', 'object_id': str(user.id), 'action': 'soft_delete'},
            source='users',
        )

    @staticmethod
    def update_self(*, user: User, data: dict) -> User:
        forbidden = set(data) - SELF_EDITABLE_FIELDS
        if forbidden:
            raise exceptions.RoleNotAllowedException(
                f'Поля недоступны для изменения: {", ".join(sorted(forbidden))}.'
            )
        for field, value in data.items():
            setattr(user, field, value)
        user.updated_by = user
        user.full_clean(exclude=['password'])
        user.save()
        return user

    @staticmethod
    def _apply_profile_data(user: User, profile_data: dict) -> None:
        if not profile_data:
            return
        profile = (
            getattr(user, 'client_profile', None)
            if user.role == Roles.CLIENT
            else (
                getattr(user, 'driver_profile', None)
                if user.role == Roles.DRIVER
                else getattr(user, 'employee_profile', None)
            )
        )
        if profile is None:
            return
        applied = {key: value for key, value in profile_data.items() if hasattr(profile, key)}
        for field, value in applied.items():
            setattr(profile, field, value)
        if applied:
            profile.save(update_fields=[*applied.keys(), 'updated_at'])

    @staticmethod
    def _check_role_assignment(actor: User, role: str) -> None:
        """Матрица прав (ТЗ, раздел 14): SuperAdmin — любые роли,
        Director — все кроме SuperAdmin, Operator — только клиентов."""
        if actor.role == Roles.SUPERADMIN or actor.is_superuser:
            return
        if actor.role == Roles.DIRECTOR and role != Roles.SUPERADMIN:
            return
        if actor.role == Roles.OPERATOR and role == Roles.CLIENT:
            return
        raise exceptions.RoleNotAllowedException()

    @staticmethod
    def _ensure_not_self(actor: User, user: User) -> None:
        if actor.id == user.id:
            raise exceptions.SelfBlockException()

    @staticmethod
    def _ensure_not_last_superadmin(user: User) -> None:
        if user.role != Roles.SUPERADMIN:
            return
        has_other = User.objects.filter(role=Roles.SUPERADMIN, is_active=True).exclude(id=user.id).exists()
        if not has_other:
            raise exceptions.LastSuperAdminException()
