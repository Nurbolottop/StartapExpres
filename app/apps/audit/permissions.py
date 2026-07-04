"""Permissions модуля audit (ТЗ, раздел 14: просмотр — SuperAdmin и Director)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewAudit(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR)
