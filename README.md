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

### Модули (все этапы Roadmap 1–8 реализованы)

| Модуль | Назначение |
|---|---|
| `apps.common` | BaseModel, Event Bus, конверт ответов, каталог ошибок, permissions, идемпотентность, шифрование ПДн, health×6 |
| `apps.users` | User (7 ролей), профили Client/Employee/Driver, JWT, device-сессии, brute-force защита |
| `apps.branches` | города и филиалы |
| `apps.audit` | append-only журнал всех доменных событий + API |
| `apps.vehicles` | типы ТС, автомобили, назначение водителей |
| `apps.warehouses` | склады → зоны → ячейки; приём/размещение/перемещение/инвентаризация/выдача, damage/lost |
| `apps.tariffs` | тарифы по направлениям, допуслуги, калькулятор стоимости |
| `apps.orders` | заказы: FSM 21 статус, история, заморозка полей, оплата, идемпотентность |
| `apps.packages` | грузовые места, QR/штрихкод (неизменяемые), фотофиксация 5 этапов, скан |
| `apps.tracking` | события трекинга заказов (immutable) |
| `apps.routes` | маршруты и точки |
| `apps.shipments` | рейсы: FSM 13 статусов, погрузка/разгрузка сканами, чек-лист старта, инциденты |
| `apps.gps` | GPS-лог, live-карта (Redis), ETA, геозоны, детекция (overspeed/long stop/offline→GPS_LOST) |
| `apps.finance` | Payment→Transaction→Invoice, касса+смены, долги (постоплата), возвраты, фин. отчёты |
| `apps.analytics` | ролевые дашборды (кэш 30 сек), отчётные срезы |
| `apps.notifications` | шаблоны в БД, 10 авто-уведомлений цепочки заказа, Celery retry 1/5/15/60 |
| `apps.integrations` | Provider Interface (SMS/Email/Telegram) — смена оператора без изменения кода |


