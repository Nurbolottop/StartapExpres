"""Селекторы accounts: все выборки пользователей проходят здесь."""
from django.db.models import QuerySet

from apps.accounts.models import User


def user_list() -> QuerySet[User]:
    return User.objects.select_related('branch')
