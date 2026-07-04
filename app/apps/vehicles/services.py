"""Сервисный слой vehicles: справочник транспорта и назначение водителей."""

from django.db import transaction

from apps.common import events
from apps.users.choices import DriverStatus, Roles
from apps.users.models import User
from apps.vehicles import exceptions
from apps.vehicles.choices import VehicleStatus
from apps.vehicles.models import Vehicle, VehicleType


class _CrudService:
    model: type
    event_prefix: str
    source = 'vehicles'

    @classmethod
    def _identity(cls, instance) -> dict:
        return {'repr': str(instance)}

    @classmethod
    @transaction.atomic
    def create(cls, *, actor, data: dict):
        instance = cls.model(created_by=actor, **data)
        instance.full_clean()
        instance.save()
        events.publish(
            f'{cls.event_prefix}.created',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'create',
                'new': cls._identity(instance),
            },
            source=cls.source,
        )
        return instance

    @classmethod
    @transaction.atomic
    def update(cls, *, actor, instance, data: dict):
        old = {field: str(getattr(instance, field)) for field in data}
        for field, value in data.items():
            setattr(instance, field, value)
        instance.updated_by = actor
        instance.full_clean()
        instance.save()
        events.publish(
            f'{cls.event_prefix}.updated',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'update',
                'old': old,
                'new': {field: str(getattr(instance, field)) for field in old},
            },
            source=cls.source,
        )
        return instance

    @classmethod
    @transaction.atomic
    def soft_delete(cls, *, actor, instance) -> None:
        instance.updated_by = actor
        instance.is_active = False
        instance.save(update_fields=['updated_by', 'is_active', 'updated_at'])
        instance.delete()
        events.publish(
            f'{cls.event_prefix}.deleted',
            {
                'actor_id': str(actor.id),
                'model': cls.model.__name__,
                'object_id': str(instance.id),
                'action': 'soft_delete',
            },
            source=cls.source,
        )


class VehicleTypeService(_CrudService):
    model = VehicleType
    event_prefix = 'vehicle_type'


class VehicleService(_CrudService):
    model = Vehicle
    event_prefix = 'vehicle'

    @classmethod
    @transaction.atomic
    def assign_driver(cls, *, actor, vehicle: Vehicle, driver: User) -> Vehicle:
        """Назначение водителя (ТЗ, раздел 09): машина активна и не в ремонте,
        водитель — активный сотрудник с ролью driver, свободен от других машин."""
        vehicle = Vehicle.objects.select_for_update().get(id=vehicle.id)

        if not vehicle.is_active or vehicle.status in (VehicleStatus.MAINTENANCE, VehicleStatus.INACTIVE):
            raise exceptions.VehicleUnavailableException()
        if driver.role != Roles.DRIVER or not driver.is_active:
            raise exceptions.DriverUnavailableException('Пользователь не является активным водителем.')

        profile = getattr(driver, 'driver_profile', None)
        if profile is None or profile.status == DriverStatus.SUSPENDED:
            raise exceptions.DriverUnavailableException('Профиль водителя отстранён или отсутствует.')

        other = Vehicle.objects.select_for_update().filter(current_driver=driver).exclude(id=vehicle.id)
        for busy_vehicle in other:
            if busy_vehicle.status == VehicleStatus.BUSY:
                raise exceptions.DriverUnavailableException('Водитель закреплён за машиной в рейсе.')
            busy_vehicle.current_driver = None
            busy_vehicle.save(update_fields=['current_driver', 'updated_at'])

        vehicle.current_driver = driver
        vehicle.updated_by = actor
        vehicle.save(update_fields=['current_driver', 'updated_by', 'updated_at'])
        profile.assigned_vehicle = vehicle
        profile.save(update_fields=['assigned_vehicle', 'updated_at'])

        events.publish(
            'vehicle.driver_assigned',
            {
                'actor_id': str(actor.id),
                'model': 'Vehicle',
                'object_id': str(vehicle.id),
                'action': 'assign_driver',
                'new': {'driver_id': str(driver.id), 'phone': driver.phone},
            },
            source=cls.source,
        )
        return vehicle

    @classmethod
    @transaction.atomic
    def unassign_driver(cls, *, actor, vehicle: Vehicle) -> Vehicle:
        vehicle = Vehicle.objects.select_for_update().get(id=vehicle.id)
        driver = vehicle.current_driver
        if driver is None:
            return vehicle
        profile = getattr(driver, 'driver_profile', None)
        if profile and profile.assigned_vehicle_id == vehicle.id:
            profile.assigned_vehicle = None
            profile.save(update_fields=['assigned_vehicle', 'updated_at'])
        vehicle.current_driver = None
        vehicle.updated_by = actor
        vehicle.save(update_fields=['current_driver', 'updated_by', 'updated_at'])
        events.publish(
            'vehicle.driver_unassigned',
            {
                'actor_id': str(actor.id),
                'model': 'Vehicle',
                'object_id': str(vehicle.id),
                'action': 'unassign_driver',
                'old': {'driver_id': str(driver.id)},
            },
            source=cls.source,
        )
        return vehicle
