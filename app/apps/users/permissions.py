"""Permissions модуля users (ТЗ, раздел 14: матрица Users)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewUsers(RolePermission):
    """Users: R — SuperAdmin, Director, Finance."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.FINANCE)


class CanManageUsers(RolePermission):
    """Users: создание/изменение — SuperAdmin, Director; Operator — только клиентов
    (ограничение по роли проверяет UserService)."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)


class CanDeleteUsers(RolePermission):
    allowed_roles = (Roles.SUPERADMIN,)


class CanManageClients(RolePermission):
    """Clients: работа с клиентами — Operator и руководство."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)
