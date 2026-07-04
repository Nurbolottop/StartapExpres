"""Permissions модуля tariffs (ТЗ, раздел 14: тарифы меняют SuperAdmin и Director)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanManageTariffs(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR)
