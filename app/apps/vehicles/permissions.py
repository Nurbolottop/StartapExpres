"""Permissions модуля vehicles (ТЗ, разделы 14, 20)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanManageVehicles(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR)


class CanAssignDriver(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)


class CanViewVehicles(RolePermission):
    allowed_roles = (
        Roles.SUPERADMIN,
        Roles.DIRECTOR,
        Roles.FINANCE,
        Roles.OPERATOR,
        Roles.WAREHOUSE,
        Roles.DRIVER,
    )
