"""Permissions модуля branches (ТЗ, раздел 14: филиалами управляет SuperAdmin)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanManageBranches(RolePermission):
    allowed_roles = (Roles.SUPERADMIN,)
