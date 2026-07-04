from django.core.validators import MinValueValidator
from django.db import models

from apps.common.models import BaseModel


class Route(BaseModel):
    """Маршрут между филиалами (ТЗ, раздел 02: ROUTES)."""

    name = models.CharField('Название', max_length=150)
    code = models.CharField('Код', max_length=20, unique=True)
    start_branch = models.ForeignKey(
        'branches.Branch', verbose_name='Старт', related_name='routes_from', on_delete=models.PROTECT
    )
    end_branch = models.ForeignKey(
        'branches.Branch', verbose_name='Финиш', related_name='routes_to', on_delete=models.PROTECT
    )
    estimated_distance = models.DecimalField(
        'Расстояние, км', max_digits=8, decimal_places=1, validators=[MinValueValidator(0)]
    )
    estimated_duration = models.PositiveIntegerField('Время в пути, мин')

    class Meta:
        verbose_name = 'Маршрут'
        verbose_name_plural = 'Маршруты'
        ordering = ('name',)
        indexes = [models.Index(fields=['start_branch', 'end_branch'])]

    def __str__(self) -> str:
        return f'{self.name} ({self.code})'


class RoutePoint(BaseModel):
    """Точка маршрута (ТЗ, раздел 02: RoutePoint; поле order переименовано
    в sequence во избежание конфликта со связью на заказы)."""

    route = models.ForeignKey(Route, verbose_name='Маршрут', related_name='points', on_delete=models.CASCADE)
    city = models.ForeignKey(
        'branches.City', verbose_name='Город', related_name='route_points', on_delete=models.PROTECT
    )
    sequence = models.PositiveSmallIntegerField('Порядок')
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)

    class Meta:
        verbose_name = 'Точка маршрута'
        verbose_name_plural = 'Точки маршрута'
        ordering = ('route', 'sequence')
        constraints = [
            models.UniqueConstraint(fields=['route', 'sequence'], name='unique_sequence_per_route'),
        ]

    def __str__(self) -> str:
        return f'{self.route.code} #{self.sequence}: {self.city.name}'
