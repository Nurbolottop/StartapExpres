from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    """Доступ только пользователям с ролью из allowed_roles.

    Суперпользователь проходит всегда.
    """

    allowed_roles: tuple[str, ...] = ()
    message = 'Недостаточно прав для выполнения операции.'

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        return user.is_superuser or user.role in self.allowed_roles


def role_required(*roles: str) -> type[RolePermission]:
    """Фабрика permission-классов: permission_classes = [role_required(Roles.ADMIN)]."""
    return type('RolePermission', (RolePermission,), {'allowed_roles': tuple(roles)})


class ActionPermissionsMixin:
    """Права на уровне action во ViewSet.

    permission_classes_by_action = {
        'create': [role_required(Roles.ADMIN)],
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
