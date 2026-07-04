# Express Delivery ERP — Backend

ERP-система управления экспресс-доставкой грузов (разрабатывается по SRS, части 01–30): клиенты, операторы, склад, водители, финансы, руководство. Полный цикл: заказ → приём груза → склад → маршрут → доставка (GPS) → выдача → финансы → аналитика.

## Стек

- Python 3.12 / Django 5.2 / Django REST Framework
- PostgreSQL 16, Redis 7, Celery (worker + beat)
- JWT (simplejwt): rotation + blacklist, device-сессии, Argon2
- OpenAPI: Swagger `/api/docs/`, Redoc `/api/redoc/`
- Docker / docker-compose (dev и prod)

## Архитектура

Модульный монолит, событийно-ориентированный (ТЗ, разделы 05, 17). Слои:

```
View (тонкий) → Serializer (I/O) → Permission → Service (бизнес-логика)
                                   → Selector (чтение) → ORM
Service → Event Bus → подписчики (audit, в будущем notifications/analytics)
```

Правила (обязательны для всех модулей):

- Запись данных — **только через Service**. View не содержит логики, Serializer не создаёт объектов.
- Каждая операция сервиса публикует доменное событие (`apps.common.events`); audit пишется подписчиком.
- Все доменные модели наследуют `apps.common.models.BaseModel` (UUID PK, created/updated_at, created/updated_by, is_active, is_deleted). Удаление — только Soft Delete; физическое — `hard_delete()`.
- Статусы/роли/типы — только через `choices.py`, никаких строк в коде.
- Права — только Permission-классы (`apps.common.permissions`, `apps/<module>/permissions.py`); `if user.role == ...` во View запрещён.
- Ошибки — коды из каталога `apps.common.errors` + иерархия `apps.common.exceptions` (BusinessException → 422, ConflictException → 409 и т.д.).
- Человекочитаемые номера — `apps.common.services.generate_number('ORD')` → `ORD-2026-000001`.

### Модули

| Модуль | Состояние | Назначение |
|---|---|---|
| `apps.common` | ✅ | BaseModel, Event Bus, конверт ответов, каталог ошибок, permissions, шифрование ПДн, health |
| `apps.users` | ✅ | User (7 ролей), профили (Client/Employee/Driver), JWT, device-сессии, brute-force защита |
| `apps.branches` | ✅ | города и филиалы |
| `apps.audit` | ✅ | append-only журнал всех доменных событий + API |
| warehouses, vehicles, тарифы | Этап 1B | склады (зоны/ячейки), транспорт, тарифы |
| orders, packages, shipments, gps, finance, analytics, notifications | Этапы 2–8 | по Roadmap ТЗ (раздел 13) |

## Единый формат API

Префикс `/api/v1/`, только JSON. Ответы (ТЗ, раздел 25):

```json
{"success": true, "message": "Success", "data": {...}, "meta": {"page": 1, "total": 254}}
{"success": false, "message": "Ошибка валидации данных.", "error": {"code": "VALIDATION_ERROR", "fields": {...}}}
```

Каждый ответ несёт заголовки `X-Request-ID`, `X-Correlation-ID`, `X-API-Version`, `X-Execution-Time`.

### Основные endpoint'ы (Этап 1A)

| Метод | URL | Доступ |
|---|---|---|
| POST | `/api/v1/auth/register/` | все (регистрация клиента) |
| POST | `/api/v1/auth/login/` · `refresh/` · `logout/` · `logout-all/` | rate limit 10/мин |
| GET/PATCH | `/api/v1/auth/me/` | авторизованные |
| POST | `/api/v1/auth/change-password/` | авторизованные |
| GET/DELETE | `/api/v1/auth/sessions/` · `sessions/{id}/` | авторизованные |
| CRUD | `/api/v1/users/` | superadmin, director (finance — чтение; operator — создание клиентов) |
| CRUD | `/api/v1/clients/` | operator, director, superadmin |
| CRUD | `/api/v1/cities/`, `/api/v1/branches/` | чтение — сотрудники, запись — superadmin |
| GET | `/api/v1/audit/` | superadmin, director |
| GET | `/api/v1/health/` (+ `/db/ /cache/ /redis/ /celery/ /storage/`) | публично |

## Безопасность (реализовано)

Argon2, пароль ≥12 (сложность), блокировка входа: 5 ошибок → 30 мин, 20 → до разблокировки SuperAdmin; device-сессии с точечным завершением; шифрование ПДн (паспорт) AES/Fernet; rate limits: аноним 100/день, user 5000/день, driver 10000/день; audit всех операций (append-only).

## Запуск

```bash
cp .envtest .env                      # заполнить SECRET_KEY и пароли
docker compose --env-file .env -f docker/docker-compose.yml up --build
```

- API: http://127.0.0.1:8084 (Swagger: `/api/docs/`)
- Суперпользователь: `docker compose --env-file .env -f docker/docker-compose.yml exec web python manage.py createsuperuser`

> Кириллица в пути ломает buildkit — запускать из ASCII-симлинка: `ln -sfn "$(pwd)" ~/.delivery-erp && cd ~/.delivery-erp`

Прод: `docker compose --env-file .env -f docker/docker-compose.prod.yml up --build -d` (gunicorn, whitenoise, celery worker + beat).

## Тесты и качество

```bash
cd app && ../.venv/bin/python -m pytest --cov=apps   # sqlite in-memory, Postgres не нужен
cd .. && .venv/bin/black app/ && .venv/bin/isort app/ && .venv/bin/flake8 app/
```

Требования ТЗ: coverage ≥90% (критические сервисы ≥95%), линтеры чистые, миграции именованные (`0001_create_users_and_profiles`), генерация миграций в Docker запрещена.

## Документация

- [docs/DEVIATIONS.md](docs/DEVIATIONS.md) — отклонения от ТЗ и разрешённые противоречия
- [docs/TECH_DEBT.md](docs/TECH_DEBT.md) — реестр технического долга (по Technical Debt Policy)

## Git

Ветки: main / develop / feature/* / bugfix/* / hotfix/*. Коммиты: conventional (`feat:`, `fix:`, `refactor:` ...).
