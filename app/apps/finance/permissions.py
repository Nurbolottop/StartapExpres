"""Permissions модуля finance (ТЗ, раздел 14: Finance CRUD — SuperAdmin/Director/Finance)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewFinance(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.FINANCE, Roles.OPERATOR)


class CanManageFinance(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.FINANCE)


class CanRefund(RolePermission):
    """Возврат — Finance, Director, SuperAdmin (ТЗ, раздел 11)."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.FINANCE)
