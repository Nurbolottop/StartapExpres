"""FSM грузового места (ТЗ, раздел 23: PACKAGE FSM)."""

from apps.common import errors
from apps.common.exceptions import ConflictException
from apps.packages.choices import PackageStatus

PACKAGE_TRANSITIONS: dict[str, frozenset[str]] = {
    PackageStatus.CREATED: frozenset({PackageStatus.RECEIVED}),
    PackageStatus.RECEIVED: frozenset({PackageStatus.CHECKED, PackageStatus.DAMAGED}),
    PackageStatus.CHECKED: frozenset({PackageStatus.STORED, PackageStatus.DAMAGED}),
    PackageStatus.STORED: frozenset(
        {PackageStatus.WAITING_LOADING, PackageStatus.DAMAGED, PackageStatus.LOST}
    ),
    PackageStatus.WAITING_LOADING: frozenset(
        {PackageStatus.LOADED, PackageStatus.DAMAGED, PackageStatus.LOST}
    ),
    PackageStatus.LOADED: frozenset({PackageStatus.IN_TRANSIT, PackageStatus.DAMAGED}),
    PackageStatus.IN_TRANSIT: frozenset({PackageStatus.UNLOADED, PackageStatus.DAMAGED, PackageStatus.LOST}),
    PackageStatus.UNLOADED: frozenset({PackageStatus.READY_FOR_PICKUP, PackageStatus.DAMAGED}),
    PackageStatus.READY_FOR_PICKUP: frozenset({PackageStatus.DELIVERED, PackageStatus.RETURNED}),
    PackageStatus.DELIVERED: frozenset({PackageStatus.RETURNED}),
    PackageStatus.RETURNED: frozenset(),
    PackageStatus.DAMAGED: frozenset({PackageStatus.RETURNED}),
    PackageStatus.LOST: frozenset(),
}


class InvalidPackageTransitionException(ConflictException):
    default_code = errors.PackageErrors.NOT_FOUND
    default_message = 'Недопустимый переход статуса груза.'


class PackageTransitionService:
    @staticmethod
    def can_change(package, to_status: str) -> bool:
        return to_status in PACKAGE_TRANSITIONS.get(package.status, frozenset())

    @classmethod
    def change(cls, *, package, to_status: str, actor) -> None:
        """Смена статуса груза внутри транзакции вызывающего сервиса."""
        if not cls.can_change(package, to_status):
            raise InvalidPackageTransitionException(
                f'Переход {package.status} → {to_status} запрещён.',
                code=errors.WarehouseErrors.INVALID_MOVEMENT,
                details={'from': package.status, 'to': to_status},
            )
        package.status = to_status
        package.updated_by = actor
        package.save(update_fields=['status', 'updated_by', 'updated_at'])
