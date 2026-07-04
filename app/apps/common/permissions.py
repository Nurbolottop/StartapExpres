"""RBAC (ТЗ, разделы 12, 14).

Никаких проверок `request.user.role == ...` во View — только Permission-классы.
Роли не сравниваются строками в бизнес-коде: используются choices из
apps.users.choices.Roles.
"""

from rest_framework.permissions import BasePermission

from apps.users.choices import Roles


class RolePermission(BasePermission):
    """Доступ пользователям с ролью из allowed_roles. SuperAdmin проходит всегда."""

    allowed_roles: tuple[str, ...] = ()
    message = 'Недостаточно прав для выполнения операции.'

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        return user.role == Roles.SUPERADMIN or user.is_superuser or user.role in self.allowed_roles


def role_required(*roles: str) -> type[RolePermission]:
    """Фабрика permission-классов: permission_classes = [role_required(Roles.DIRECTOR)]."""
    return type('RolePermission', (RolePermission,), {'allowed_roles': tuple(roles)})


class IsSuperAdmin(RolePermission):
    allowed_roles = (Roles.SUPERADMIN,)


class IsDirector(RolePermission):
    allowed_roles = (Roles.DIRECTOR,)


class IsFinance(RolePermission):
    allowed_roles = (Roles.FINANCE,)


class IsOperator(RolePermission):
    allowed_roles = (Roles.OPERATOR,)


class IsWarehouse(RolePermission):
    allowed_roles = (Roles.WAREHOUSE,)


class IsDriver(RolePermission):
    allowed_roles = (Roles.DRIVER,)


class IsClient(RolePermission):
    allowed_roles = (Roles.CLIENT,)


class IsOwner(BasePermission):
    """Object-level ownership: объект принадлежит пользователю (ТЗ, раздел 14).

    Модель должна определять owner-поле; по умолчанию ищутся user/client/created_by.
    """

    owner_fields = ('user', 'client', 'created_by')

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if user.role == Roles.SUPERADMIN or user.is_superuser:
            return True
        for field_name in self.owner_fields:
            owner = getattr(obj, field_name, None)
            if owner is not None:
                owner_id = getattr(owner, 'user_id', None) or getattr(owner, 'id', None)
                return owner_id == user.id
        return False


class ActionPermissionsMixin:
    """Права на уровне action во ViewSet.

    permission_classes_by_action = {
        'create': [IsOperator],
        '__default__': [IsAuthenticated],
    }
    """

    permission_classes_by_action: dict[str, list] = {}

    def get_permissions(self):
        permission_classes = self.permission_classes_by_action.get(
            self.action,
            self.permission_classes_by_action.get('__default__', self.permission_classes),
        )
        return [permission() for permission in permission_classes]
