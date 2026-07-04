# Express Delivery ERP — Backend

ERP-система управления экспресс-доставкой грузов: клиенты, операторы, склад, водители, финансы, руководство. Полный цикл: заказ → приём груза → склад → маршрут → доставка (GPS) → выдача → финансы → аналитика.

## Стек

- Python 3.12 / Django 5.2 / Django REST Framework
- PostgreSQL 16, Redis 7
- JWT-аутентификация (simplejwt, refresh rotation + blacklist)
- Celery (worker + beat)
- OpenAPI/Swagger (drf-spectacular)
- Docker / docker-compose (dev и prod)

## Архитектура

Модульный монолит. Каждый Django-app — bounded context со слоями:

```
models (тонкие) → selectors (чтение) → services (бизнес-логика/запись)
                → serializers (I/O) → views (тонкие)
```

Правила:

- Бизнес-логика — только в `services.py`. Во views — никакой логики.
- Сложные выборки — в `selectors.py`.
- Чистый CRUD без доменной логики (справочники) допускает стандартный `ModelSerializer` + `ModelViewSet`.
- Все доменные модели наследуют `apps.common.models.BaseModel` (UUID PK + created_at/updated_at).
- Сервисы бросают `apps.common.exceptions.ApplicationError` (и наследников) — HTTP-статус определяет класс исключения.

### Модули

| Модуль | Назначение |
|---|---|
| `apps.common` | базовые модели, единый формат ошибок, permissions, пагинация, request-id middleware, health-check |
| `apps.accounts` | пользователи, роли, JWT-аутентификация |
| `apps.branches` | филиалы компании |
| `apps.orders` | (план) заказы, груз, статусная машина |
| `apps.warehouse` | (план) приёмка, размещение, склад |
| `apps.logistics` | (план) маршруты, водители, GPS |
| `apps.finance` | (план) тарифы, платежи, взаиморасчёты |
| `apps.analytics` | (план) отчёты и дашборды |

### Роли

`client`, `operator`, `warehouse`, `courier`, `finance`, `manager`, `admin` — поле `User.role`. Доступ в API — через `role_required(...)` из `apps.common.permissions`.

## Единый стиль API

- Базовый префикс: `/api/v1/`
- Аутентификация: `Authorization: Bearer <access>`
- Документация: `GET /api/docs/` (Swagger UI), схема — `GET /api/schema/`
- Health-check: `GET /api/v1/health/`
- Формат ошибок единый:

```json
{"error": {"code": "validation_error", "message": "Ошибка валидации данных.", "details": {"phone": ["..."]}}}
```

### Основные endpoint'ы

| Метод | URL | Описание | Доступ |
|---|---|---|---|
| POST | `/api/v1/auth/login/` | вход (phone + password) → access/refresh/user | все |
| POST | `/api/v1/auth/refresh/` | обновление access-токена | все |
| POST | `/api/v1/auth/logout/` | выход (blacklist refresh) | авторизованные |
| GET/PATCH | `/api/v1/auth/me/` | свой профиль | авторизованные |
| POST | `/api/v1/auth/password/change/` | смена пароля | авторизованные |
| CRUD | `/api/v1/users/` | управление пользователями | admin, manager |
| CRUD | `/api/v1/branches/` | справочник филиалов | чтение — все, запись — admin/manager |

## Запуск

### 1. Переменные окружения

```bash
cp .envtest .env   # затем отредактируй SECRET_KEY и пароли
```

### 2. Разработка (docker)

```bash
docker compose --env-file .env -f docker/docker-compose.yml up --build
```

> Если buildkit падает с ошибкой `header key ... non-printable ASCII characters` — путь к проекту содержит кириллицу. Создай ASCII-симлинк и запускай из него:
> `ln -sfn "$(pwd)" ~/.delivery-erp && cd ~/.delivery-erp`

- API: http://127.0.0.1:8084 (Swagger: http://127.0.0.1:8084/api/docs/)
- Postgres снаружи: `localhost:5433`, Redis: `localhost:6389`
- Миграции и collectstatic выполняются автоматически (entrypoint)

Создание суперпользователя:

```bash
docker compose --env-file .env -f docker/docker-compose.yml exec web python manage.py createsuperuser
```

### 3. Продакшн

```bash
docker compose --env-file .env -f docker/docker-compose.prod.yml up --build -d
```

Web слушает `127.0.0.1:8000` (gunicorn, 4 воркера), статику отдаёт whitenoise, media — volume `<PROJECT_NAME>_media_data` (раздаётся host-nginx). Celery worker и beat подняты отдельными контейнерами.

### 4. Локальная разработка без docker

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
cd app && ../.venv/bin/python manage.py runserver   # требуется Postgres/Redis
```

## Тесты

```bash
cd app && ../.venv/bin/python -m pytest
```

Тесты идут на sqlite in-memory (`core.settings.test`), Postgres/Redis не требуются.

## Правила разработки

1. Новые миграции создаются в разработке и коммитятся; в контейнере выполняется только `migrate`.
2. Новая доменная сущность = наследник `BaseModel`; записи с историей (заказы, платежи) — `SoftDeleteModel`.
3. Каждое изменение покрывается тестами; PR без зелёного `pytest` не мержится.
4. Секреты — только в `.env` (не коммитится).
