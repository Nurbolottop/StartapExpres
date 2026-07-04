"""Permissions модуля warehouses (ТЗ, разделы 14, 20)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewWarehouses(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.FINANCE, Roles.OPERATOR, Roles.WAREHOUSE)


class CanManageWarehouses(RolePermission):
    """Создание/закрытие складов — руководство."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR)


class CanManageWarehouseStructure(RolePermission):
    """Зоны и ячейки — руководство и склад."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.WAREHOUSE)
