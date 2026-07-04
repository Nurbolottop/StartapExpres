"""Permissions модуля orders (ТЗ, раздел 14: матрица Orders)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewOrders(RolePermission):
    """R: все роли, кроме driver (получит доступ через рейсы). Скоупинг —
    в OrderSelector.for_user."""

    allowed_roles = (
        Roles.SUPERADMIN,
        Roles.DIRECTOR,
        Roles.FINANCE,
        Roles.OPERATOR,
        Roles.WAREHOUSE,
        Roles.CLIENT,
    )


class CanCreateOrder(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.CLIENT)


class CanEditOrder(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.CLIENT)


class CanConfirmOrder(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)


class CanCancelOrder(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.CLIENT)


class CanPayOrder(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.FINANCE)


class CanChangeOrderStatus(RolePermission):
    """Детальная проверка роли на конкретный переход — в TransitionService."""

    allowed_roles = (
        Roles.SUPERADMIN,
        Roles.DIRECTOR,
        Roles.OPERATOR,
        Roles.WAREHOUSE,
        Roles.FINANCE,
        Roles.DRIVER,
    )
