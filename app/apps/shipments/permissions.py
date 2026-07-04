"""Permissions модуля shipments (ТЗ, разделы 09, 14)."""

from apps.common.permissions import RolePermission
from apps.users.choices import Roles


class CanViewShipments(RolePermission):
    allowed_roles = (
        Roles.SUPERADMIN,
        Roles.DIRECTOR,
        Roles.FINANCE,
        Roles.OPERATOR,
        Roles.WAREHOUSE,
        Roles.DRIVER,
    )


class CanCreateShipment(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR)


class CanLoadShipment(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.WAREHOUSE)


class CanDriveShipment(RolePermission):
    """Старт/прибытие — водитель своего рейса или офис."""

    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.DRIVER)


class CanReportIncident(RolePermission):
    allowed_roles = (Roles.SUPERADMIN, Roles.DIRECTOR, Roles.OPERATOR, Roles.DRIVER)
