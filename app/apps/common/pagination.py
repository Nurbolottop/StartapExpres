from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DefaultPageNumberPagination(PageNumberPagination):
    """Пагинация с meta-блоком (ТЗ, раздел 25)."""

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data) -> Response:
        return Response(
            {
                'success': True,
                'message': 'Success',
                'data': data,
                'meta': {
                    'page': self.page.number,
                    'page_size': self.page.paginator.per_page,
                    'total': self.page.paginator.count,
                    'pages': self.page.paginator.num_pages,
                    'next': self.page.has_next(),
                    'previous': self.page.has_previous(),
                },
            }
        )

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'message': {'type': 'string'},
                'data': schema,
                'meta': {
                    'type': 'object',
                    'properties': {
                        'page': {'type': 'integer'},
                        'page_size': {'type': 'integer'},
                        'total': {'type': 'integer'},
                        'pages': {'type': 'integer'},
                        'next': {'type': 'boolean'},
                        'previous': {'type': 'boolean'},
                    },
                },
            },
        }
