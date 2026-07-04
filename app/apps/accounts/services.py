"""Сервисный слой accounts: вся запись/изменение пользователей проходит здесь."""
from django.contrib.auth.password_validation import validate_password

from apps.accounts.models import User
from apps.branches.models import Branch
from apps.common.exceptions import ApplicationError

# Поля, которые разрешено менять через user_update
_UPDATABLE_FIELDS = frozenset(
    {'phone', 'email', 'last_name', 'first_name', 'middle_name', 'role', 'branch', 'is_active'}
)
# Поля профиля, которые пользователь может менять сам
PROFILE_FIELDS = frozenset({'email', 'last_name', 'first_name', 'middle_name'})


def user_create(
    *,
    phone: str,
    password: str,
    role: str,
    last_name: str = '',
    first_name: str = '',
    middle_name: str = '',
    email: str = '',
    branch: Branch | None = None,
) -> User:
    user = User(
        phone=phone,
        role=role,
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name,
        email=email,
        branch=branch,
    )
    validate_password(password, user)
    user.set_password(password)
    user.full_clean(exclude=['password'])
    user.save()
    return user


def user_update(*, user: User, data: dict) -> User:
    forbidden = set(data) - _UPDATABLE_FIELDS
    if forbidden:
        raise ApplicationError(
            f'Поля недоступны для изменения: {", ".join(sorted(forbidden))}.',
            code='fields_not_updatable',
        )
    for field, value in data.items():
        setattr(user, field, value)
    user.full_clean(exclude=['password'])
    user.save(update_fields=[*data.keys(), 'updated_at'])
    return user


def user_deactivate(*, user: User) -> User:
    """Пользователи не удаляются физически — на них будут ссылаться заказы."""
    user.is_active = False
    user.save(update_fields=['is_active', 'updated_at'])
    return user


def user_change_password(*, user: User, old_password: str, new_password: str) -> User:
    if not user.check_password(old_password):
        raise ApplicationError('Текущий пароль указан неверно.', code='invalid_password')
    validate_password(new_password, user)
    user.set_password(new_password)
    user.save(update_fields=['password', 'updated_at'])
    return user
