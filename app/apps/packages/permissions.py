"""Permissions модуля packages (ТЗ, раздел 14: матрица Packages)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewPackages(RolePermission):
    allowed_roles = (
        Roles.SUPERADMIN,
        Roles.DIRECTOR,
        Roles.FINANCE,
        Roles.OPERATOR,
        Roles.WAREHOUSE,
        Roles.CLIENT,
    )


class CanManagePackages(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.WAREHOUSE)


class CanScanPackages(RolePermission):
    """Сканирование — склад и водители (ТЗ, раздел 14)."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.WAREHOUSE, Roles.DRIVER)
