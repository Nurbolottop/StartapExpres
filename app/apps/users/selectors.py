"""Селекторы users: только чтение (ТЗ, раздел 05)."""

from django.db.models import QuerySet

from apps.users.choices import Roles
from apps.users.models import DeviceSession, User


class UserSelector:
    @staticmethod
    def list() -> QuerySet[User]:
        return User.objects.select_related('client_profile', 'employee_profile__branch', 'driver_profile')

    @staticmethod
    def clients() -> QuerySet[User]:
        return UserSelector.list().filter(role=Roles.CLIENT)

    @staticmethod
    def active_sessions(user: User) -> QuerySet[DeviceSession]:
        return DeviceSession.objects.filter(user=user, is_active=True)
