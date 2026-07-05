"""Генератор полного API-справочника (docs/API_REFERENCE.md) из OpenAPI-схемы.

Запуск:  cd app && DJANGO_SETTINGS_MODULE=core.settings.test \
         python manage.py spectacular --format openapi-json --file /tmp/schema.json && \
         python ../scripts/generate_api_reference.py /tmp/schema.json ../docs/API_REFERENCE.md
"""
import json
import sys

METHOD_ORDER = {'get': 0, 'post': 1, 'patch': 2, 'put': 3, 'delete': 4}


def resolve(schema: dict, node: dict) -> dict:
    while isinstance(node, dict) and '$ref' in node:
        ref = node['$ref'].split('/')[-1]
        node = schema['components']['schemas'].get(ref, {})
    return node


def type_of(schema: dict, prop: dict) -> str:
    prop = resolve(schema, prop)
    if 'enum' in prop:
        values = ' \\| '.join(f'`{value}`' for value in prop['enum'] if value is not None)
        return f'enum: {values}'
    kind = prop.get('type', 'object')
    if kind == 'array':
        return f'array[{type_of(schema, prop.get("items", {}))}]'
    if prop.get('format'):
        return f'{kind} ({prop["format"]})'
    return kind


def body_fields(schema: dict, operation: dict) -> list[tuple[str, str, bool, str]]:
    body = operation.get('requestBody', {})
    content = body.get('content', {})
    media = content.get('application/json') or next(iter(content.values()), {})
    node = resolve(schema, media.get('schema', {}))
    required = set(node.get('required', []))
    rows = []
    for name, prop in node.get('properties', {}).items():
        raw = resolve(schema, prop)
        if raw.get('readOnly'):
            continue
        title = raw.get('title', '') or raw.get('description', '')
        rows.append((name, type_of(schema, prop), name in required, title))
    return rows


def response_fields(schema: dict, operation: dict) -> list[tuple[str, str, str]]:
    for code in ('200', '201'):
        content = operation.get('responses', {}).get(code, {}).get('content', {})
        media = content.get('application/json')
        if not media:
            continue
        node = resolve(schema, media.get('schema', {}))
        if node.get('type') == 'array':
            node = resolve(schema, node.get('items', {}))
        # разворачиваем конверт пагинации
        props = node.get('properties', {})
        if set(props) >= {'success', 'data'}:
            node = resolve(schema, props['data'])
            if node.get('type') == 'array':
                node = resolve(schema, node.get('items', {}))
            props = node.get('properties', {})
        return [
            (name, type_of(schema, prop), resolve(schema, prop).get('title', ''))
            for name, prop in list(props.items())[:25]
        ]
    return []


def main(schema_path: str, out_path: str) -> None:
    schema = json.load(open(schema_path))
    tag_descriptions = {tag['name']: tag.get('description', '') for tag in schema.get('tags', [])}

    grouped: dict[str, list] = {}
    for path, methods in schema['paths'].items():
        for method, operation in methods.items():
            if method not in METHOD_ORDER:
                continue
            tag = (operation.get('tags') or ['other'])[0]
            grouped.setdefault(tag, []).append((path, method, operation))

    lines = [
        '# API Reference — Express Delivery ERP',
        '',
        '> Сгенерировано из OpenAPI-схемы (`scripts/generate_api_reference.py`).',
        '> Живая версия с примерами: https://expres.zeastudio.su/api/docs/',
        '',
        'Base URL: `https://expres.zeastudio.su/api/v1/` · Авторизация: `Authorization: Bearer <access>`.',
        'Все ответы — в конверте `{"success", "message", "data", "meta"}`;',
        'ошибки — `{"success": false, "message", "error": {"code", "details"|"fields"}}`.',
        '',
    ]

    lines.append('## Содержание\n')
    for tag in sorted(grouped):
        lines.append(f'- [{tag}](#{tag}) — {tag_descriptions.get(tag, "")}')
    lines.append('')

    for tag in sorted(grouped):
        lines.append(f'\n---\n\n## {tag}\n')
        if tag_descriptions.get(tag):
            lines.append(f'{tag_descriptions[tag]}\n')
        operations = sorted(grouped[tag], key=lambda item: (item[0], METHOD_ORDER[item[1]]))
        for path, method, operation in operations:
            summary = operation.get('summary', '')
            lines.append(f'### `{method.upper()} {path}`\n')
            if summary:
                lines.append(f'**{summary}**\n')
            description = (operation.get('description') or '').strip()
            if description and description != summary:
                lines.append(f'{description}\n')

            params = [p for p in operation.get('parameters', []) if p.get('in') == 'query']
            if params:
                lines.append('Query-параметры:\n')
                lines.append('| Параметр | Тип | Описание |')
                lines.append('|---|---|---|')
                for param in params:
                    ptype = type_of(schema, param.get('schema', {}))
                    lines.append(f"| `{param['name']}` | {ptype} | {param.get('description', '')} |")
                lines.append('')

            fields = body_fields(schema, operation)
            if fields:
                lines.append('Тело запроса (JSON):\n')
                lines.append('| Поле | Тип | Обяз. | Описание |')
                lines.append('|---|---|---|---|')
                for name, ftype, required, title in fields:
                    mark = 'да' if required else 'нет'
                    lines.append(f'| `{name}` | {ftype} | {mark} | {title} |')
                lines.append('')

            resp = response_fields(schema, operation)
            if resp:
                lines.append('Ответ (`data`):\n')
                lines.append('| Поле | Тип | Описание |')
                lines.append('|---|---|---|')
                for name, ftype, title in resp:
                    lines.append(f'| `{name}` | {ftype} | {title} |')
                lines.append('')

    open(out_path, 'w').write('\n'.join(lines) + '\n')
    total = sum(len(ops) for ops in grouped.values())
    print(f'Готово: {total} операций, {len(grouped)} разделов → {out_path}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
