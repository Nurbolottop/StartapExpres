"""Русская автодокументация OpenAPI (ТЗ, раздел 18).

Endpoint'ы без явного summary получают русское описание, собранное из
действия и verbose_name модели.
"""

from drf_spectacular.openapi import AutoSchema

ACTION_SUMMARIES = {
    'list': 'Список: {plural}',
    'retrieve': 'Детально: {single}',
    'create': 'Создание: {single}',
    'update': 'Полное изменение: {single}',
    'partial_update': 'Изменение: {single}',
    'destroy': 'Удаление (soft delete): {single}',
}

METHOD_SUMMARIES = {
    'GET': 'Получение данных',
    'POST': 'Создание/выполнение операции',
    'PATCH': 'Частичное изменение',
    'PUT': 'Полное изменение',
    'DELETE': 'Удаление',
}


class RussianAutoSchema(AutoSchema):
    def _model_names(self) -> tuple[str, str]:
        serializer_class = getattr(self.view, 'serializer_class', None)
        model = getattr(getattr(serializer_class, 'Meta', None), 'model', None)
        if model is None:
            return ('объект', 'объекты')
        return (str(model._meta.verbose_name), str(model._meta.verbose_name_plural))

    def get_summary(self):
        explicit = super().get_summary()
        if explicit:
            return explicit
        single, plural = self._model_names()
        action = getattr(self.view, 'action', None)
        template = ACTION_SUMMARIES.get(action)
        if template:
            return template.format(single=single, plural=plural)
        return METHOD_SUMMARIES.get(self.method, '')

    def get_description(self):
        explicit = super().get_description()
        if explicit:
            return explicit
        single, plural = self._model_names()
        action = getattr(self.view, 'action', None)
        if action == 'list':
            return (
                f'Возвращает страницу списка «{plural}». Поддерживает `?page=`, '
                f'`?page_size=`, `?search=`, `?ordering=` и фильтры (см. параметры).'
            )
        if action == 'destroy':
            return 'Мягкое удаление (Soft Delete): запись скрывается, но остаётся в базе.'
        return ''
