"""Единый конверт ответов API (ТЗ, раздел 25)."""

from rest_framework.renderers import JSONRenderer

_STATUS_MESSAGES = {
    200: 'Success',
    201: 'Created successfully',
    204: 'Deleted successfully',
}


class EnvelopeJSONRenderer(JSONRenderer):
    """Оборачивает все успешные ответы в {"success", "message", "data", "meta"}.

    Ошибки уже приходят в конверте из exception_handler и не трогаются.
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context.get('response')
        status_code = response.status_code if response else 200

        if isinstance(data, dict) and 'success' in data and ('error' in data or 'data' in data):
            payload = data  # уже конверт (ошибка или пагинация)
        else:
            payload = {
                'success': status_code < 400,
                'message': _STATUS_MESSAGES.get(status_code, 'Success'),
                'data': data,
            }
        return super().render(payload, accepted_media_type, renderer_context)
