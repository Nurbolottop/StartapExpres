# API Reference — Express Delivery ERP

> Сгенерировано из OpenAPI-схемы (`scripts/generate_api_reference.py`).
> Живая версия с примерами: https://expres.zeastudio.su/api/docs/

Base URL: `https://expres.zeastudio.su/api/v1/` · Авторизация: `Authorization: Bearer <access>`.
Все ответы — в конверте `{"success", "message", "data", "meta"}`;
ошибки — `{"success": false, "message", "error": {"code", "details"|"fields"}}`.

## Содержание

- [audit](#audit) — Журнал аудита (только чтение)
- [auth](#auth) — Регистрация, вход, JWT-токены, профиль, сессии устройств
- [branches](#branches) — Филиалы компании
- [cities](#cities) — Справочник городов
- [clients](#clients) — Работа операторов с клиентами
- [dashboard](#dashboard) — Ролевой дашборд
- [finance](#finance) — Платежи, счета, касса, задолженности, возвраты, финансовые отчёты
- [gps](#gps) — GPS-мониторинг: координаты водителей, онлайн-карта, история, геозоны
- [health](#health) — Проверки живости сервиса и зависимостей
- [notifications](#notifications) — Уведомления и шаблоны
- [orders](#orders) — Заказы: создание, подтверждение, оплата, статусы (FSM), история
- [packages](#packages) — Грузовые места: QR/штрихкоды, фотофиксация, сканирование
- [reports](#reports) — Аналитические отчёты
- [routes](#routes) — Маршруты между филиалами
- [shipments](#shipments) — Рейсы: состав, погрузка/разгрузка по сканам, жизненный цикл, инциденты
- [tariffs](#tariffs) — Тарифы, дополнительные услуги, калькулятор стоимости
- [users](#users) — Управление пользователями (SuperAdmin/Director)
- [vehicles](#vehicles) — Автопарк и назначение водителей
- [warehouse-operations](#warehouse-operations) — Складские процессы: приём, размещение, перемещение, инвентаризация, выдача
- [warehouses](#warehouses) — Склады, зоны и ячейки хранения


---

## audit

Журнал аудита (только чтение)

### `GET /api/v1/audit/`

**Список: Журнал аудита**

Журнал аудита: только чтение (ТЗ, раздел 12).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `action` | string |  |
| `date_from` | string (date) |  |
| `date_to` | string (date) |  |
| `event_type` | string |  |
| `ip` | string |  |
| `model` | string |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `user` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `user` | string (uuid) | Пользователь |
| `user_phone` | string |  |
| `role` | string | Роль |
| `model` | string | Модель |
| `object_uuid` | string | ID объекта |
| `action` | string | Действие |
| `event_type` | string | Тип события |
| `old_data` | object | Старые данные |
| `new_data` | object | Новые данные |
| `ip` | string |  |
| `user_agent` | string |  |
| `request_id` | string |  |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/audit/{id}/`

**Детально: Запись аудита**

Журнал аудита: только чтение (ТЗ, раздел 12).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `user` | string (uuid) | Пользователь |
| `user_phone` | string |  |
| `role` | string | Роль |
| `model` | string | Модель |
| `object_uuid` | string | ID объекта |
| `action` | string | Действие |
| `event_type` | string | Тип события |
| `old_data` | object | Старые данные |
| `new_data` | object | Новые данные |
| `ip` | string |  |
| `user_agent` | string |  |
| `request_id` | string |  |
| `created_at` | string (date-time) | Создано |


---

## auth

Регистрация, вход, JWT-токены, профиль, сессии устройств

### `POST /api/v1/auth/change-password/`

**Смена своего пароля**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `old_password` | string | да |  |
| `new_password` | string | да |  |

### `GET /api/v1/auth/devices/`

**Мои push-устройства**

Привязка FCM/APNs-токена устройства к пользователю (push-уведомления).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `device_id` | string | Идентификатор устройства |
| `platform` | enum: `android` \| `ios` |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/auth/devices/`

**Регистрация push-токена устройства**

Привязка FCM/APNs-токена устройства к пользователю (push-уведомления).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `fcm_token` | string | да |  |
| `platform` | enum: `android` \| `ios` | да | * `android` - Android
* `ios` - iOS |
| `device_id` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `device_id` | string | Идентификатор устройства |
| `platform` | enum: `android` \| `ios` |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/auth/devices/{device_id}/`

**Удаление push-токена устройства**

Отвязка push-токена (вызывается при logout).

### `POST /api/v1/auth/login/`

**Вход по телефону и паролю**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |
| `password` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `access` | string |  |
| `refresh` | string |  |
| `user` | object |  |

### `POST /api/v1/auth/logout-all/`

**Выход со всех устройств**

### `POST /api/v1/auth/logout/`

**Выход (blacklist refresh-токена)**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `refresh` | string | да |  |

### `GET /api/v1/auth/me/`

**Мой профиль**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `PATCH /api/v1/auth/me/`

**Обновление своего профиля**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `email` | string (email) | нет |  |
| `last_name` | string | нет |  |
| `first_name` | string | нет |  |
| `middle_name` | string | нет |  |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `timezone` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `POST /api/v1/auth/password-reset/confirm/`

**Восстановление пароля: установка нового по SMS-коду**

Неверный/истёкший код — 400 AUTH_007 (максимум 5 попыток). После смены пароля все сессии и refresh-токены отзываются.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |
| `code` | string | да |  |
| `new_password` | string | да |  |

### `POST /api/v1/auth/password-reset/request/`

**Восстановление пароля: запрос SMS-кода**

Ответ всегда успешный — существование номера не раскрывается. Код живёт 10 минут, повторный запрос — не чаще раза в минуту (429 AUTH_008).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |

### `POST /api/v1/auth/refresh/`

**Создание/выполнение операции**

Обновление access-токена (simplejwt, rotation + blacklist).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `refresh` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `access` | string |  |
| `refresh` | string |  |

### `POST /api/v1/auth/register/`

**Регистрация клиента**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |
| `password` | string | да |  |
| `first_name` | string | нет |  |
| `last_name` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `access` | string |  |
| `refresh` | string |  |
| `user` | object |  |

### `GET /api/v1/auth/sessions/`

**Мои активные сессии**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `ip` | string |  |
| `user_agent` | string |  |
| `login_at` | string (date-time) | Вход |
| `last_activity` | string (date-time) | Последняя активность |
| `is_active` | boolean | Активен |

### `DELETE /api/v1/auth/sessions/{session_id}/`

**Завершить сессию устройства**

### `POST /api/v1/auth/verify/confirm/`

**Верификация телефона: подтверждение кода**

Успех — is_verified=true. Неверный/истёкший код — 400 AUTH_007.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |
| `code` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `POST /api/v1/auth/verify/request/`

**Верификация телефона: запрос SMS-кода**

Ответ всегда успешный. Для уже подтверждённого номера SMS не шлётся.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |


---

## branches

Филиалы компании

### `GET /api/v1/branches/`

**Список: Филиалы**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `city` | string (uuid) |  |
| `is_active` | boolean |  |
| `is_main` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `is_main` | boolean | Главный филиал |
| `opening_time` | string (time) | Открытие |
| `closing_time` | string (time) | Закрытие |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/branches/`

**Создание: Филиал**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `city` | string (uuid) | да | Город |
| `name` | string | да | Название |
| `code` | string | да | Код |
| `address` | string | нет | Адрес |
| `phone` | string | нет | Телефон |
| `email` | string (email) | нет |  |
| `is_main` | boolean | нет | Главный филиал |
| `opening_time` | string (time) | нет | Открытие |
| `closing_time` | string (time) | нет | Закрытие |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `is_main` | boolean | Главный филиал |
| `opening_time` | string (time) | Открытие |
| `closing_time` | string (time) | Закрытие |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/branches/{id}/`

**Детально: Филиал**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `is_main` | boolean | Главный филиал |
| `opening_time` | string (time) | Открытие |
| `closing_time` | string (time) | Закрытие |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/branches/{id}/`

**Изменение: Филиал**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `city` | string (uuid) | нет | Город |
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `address` | string | нет | Адрес |
| `phone` | string | нет | Телефон |
| `email` | string (email) | нет |  |
| `is_main` | boolean | нет | Главный филиал |
| `opening_time` | string (time) | нет | Открытие |
| `closing_time` | string (time) | нет | Закрытие |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `is_main` | boolean | Главный филиал |
| `opening_time` | string (time) | Открытие |
| `closing_time` | string (time) | Закрытие |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/branches/{id}/`

**Удаление (soft delete): Филиал**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.


---

## cities

Справочник городов

### `GET /api/v1/cities/`

**Список: Города**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `country` | string |  |
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `country` | string | Страна |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/cities/`

**Создание: Город**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название |
| `code` | string | да | Код |
| `country` | string | нет | Страна |
| `latitude` | string (decimal) | нет | Широта |
| `longitude` | string (decimal) | нет | Долгота |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `country` | string | Страна |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/cities/{id}/`

**Детально: Город**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `country` | string | Страна |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/cities/{id}/`

**Изменение: Город**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `country` | string | нет | Страна |
| `latitude` | string (decimal) | нет | Широта |
| `longitude` | string (decimal) | нет | Долгота |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `country` | string | Страна |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/cities/{id}/`

**Удаление (soft delete): Город**

Базовый ViewSet справочников: чтение — сотрудникам, запись — SuperAdmin.


---

## clients

Работа операторов с клиентами

### `GET /api/v1/clients/`

**Список: Пользователи**

Работа операторов с клиентами (ТЗ, раздел 03: /clients).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `POST /api/v1/clients/`

**Создание клиента**

Работа операторов с клиентами (ТЗ, раздел 03: /clients).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |
| `email` | string (email) | нет |  |
| `username` | string | нет |  |
| `last_name` | string | нет |  |
| `first_name` | string | нет |  |
| `middle_name` | string | нет |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` | да | * `client` - Клиент
* `operator` - Оператор
* `warehouse` - Сотрудник склада
* `driver` - Водитель
* `finance` - Финансист
* `director` - Директор
* `superadmin` - Суперадминистратор |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `timezone` | string | нет |  |
| `is_active` | boolean | нет |  |
| `is_verified` | boolean | нет |  |
| `company_name` | string | нет |  |
| `passport_number` | string | нет |  |
| `address` | string | нет |  |
| `notes` | string | нет |  |
| `discount_percent` | string (decimal) | нет |  |
| `branch` | string (uuid) | нет |  |
| `department` | string | нет |  |
| `position` | string | нет |  |
| `hired_at` | string (date) | нет |  |
| `salary` | string (decimal) | нет |  |
| `driver_license` | string | нет |  |
| `license_expiry_date` | string (date) | нет |  |
| `medical_certificate` | string | нет |  |
| `experience_years` | integer | нет |  |
| `password` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `GET /api/v1/clients/{id}/`

**Детально: Пользователь**

Работа операторов с клиентами (ТЗ, раздел 03: /clients).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `PATCH /api/v1/clients/{id}/`

**Изменение клиента**

Работа операторов с клиентами (ТЗ, раздел 03: /clients).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | нет |  |
| `email` | string (email) | нет |  |
| `username` | string | нет |  |
| `last_name` | string | нет |  |
| `first_name` | string | нет |  |
| `middle_name` | string | нет |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` | нет | * `client` - Клиент
* `operator` - Оператор
* `warehouse` - Сотрудник склада
* `driver` - Водитель
* `finance` - Финансист
* `director` - Директор
* `superadmin` - Суперадминистратор |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `timezone` | string | нет |  |
| `is_active` | boolean | нет |  |
| `is_verified` | boolean | нет |  |
| `company_name` | string | нет |  |
| `passport_number` | string | нет |  |
| `address` | string | нет |  |
| `notes` | string | нет |  |
| `discount_percent` | string (decimal) | нет |  |
| `branch` | string (uuid) | нет |  |
| `department` | string | нет |  |
| `position` | string | нет |  |
| `hired_at` | string (date) | нет |  |
| `salary` | string (decimal) | нет |  |
| `driver_license` | string | нет |  |
| `license_expiry_date` | string (date) | нет |  |
| `medical_certificate` | string | нет |  |
| `experience_years` | integer | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |


---

## dashboard

Ролевой дашборд

### `GET /api/v1/dashboard/`

**Дашборд по роли**

Ролевой дашборд (ТЗ, раздел 18): каждая роль видит свои показатели.


---

## finance

Платежи, счета, касса, задолженности, возвраты, финансовые отчёты

### `GET /api/v1/cashboxes/`

**Список: Кассы**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `balance` | string (decimal) | Баланс |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/cashboxes/{id}/`

**Детально: Касса**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `balance` | string (decimal) | Баланс |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/cashboxes/{id}/close-session/`

**Закрыть смену**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `cashbox` | string (uuid) | Касса |
| `cashier` | string (uuid) | Кассир |
| `cashier_name` | string |  |
| `opened_at` | string (date-time) | Открыта |
| `closed_at` | string (date-time) | Закрыта |
| `opening_balance` | string (decimal) | Остаток на открытие |
| `closing_balance` | string (decimal) | Остаток на закрытие |

### `POST /api/v1/cashboxes/{id}/expense/`

**Расход из кассы**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `amount` | string (decimal) | да |  |
| `comment` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `cashbox` | string (uuid) | Касса |
| `payment` | string (uuid) | Платёж |
| `amount` | string (decimal) | Сумма |
| `type` | enum: `income` \| `expense` \| `refund` \| `transfer` \| `correction` |  |
| `comment` | string | Комментарий |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/cashboxes/{id}/open-session/`

**Открыть смену**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `cashbox` | string (uuid) | Касса |
| `cashier` | string (uuid) | Кассир |
| `cashier_name` | string |  |
| `opened_at` | string (date-time) | Открыта |
| `closed_at` | string (date-time) | Закрыта |
| `opening_balance` | string (decimal) | Остаток на открытие |
| `closing_balance` | string (decimal) | Остаток на закрытие |

### `GET /api/v1/cashboxes/{id}/transactions/`

**Транзакции кассы**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `cashbox` | string (uuid) | Касса |
| `payment` | string (uuid) | Платёж |
| `amount` | string (decimal) | Сумма |
| `type` | enum: `income` \| `expense` \| `refund` \| `transfer` \| `correction` |  |
| `comment` | string | Комментарий |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/debts/`

**Список: Задолженности**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `closed` \| `open` \| `overdue` \| `partially_paid` | * `open` - Открыт
* `partially_paid` - Частично погашен
* `closed` - Закрыт
* `overdue` - Просрочен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `amount` | string (decimal) | Сумма долга |
| `paid_amount` | string (decimal) | Погашено |
| `due_date` | string (date) | Срок оплаты |
| `status` | enum: `open` \| `partially_paid` \| `closed` \| `overdue` |  |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/debts/{id}/`

**Детально: Задолженность**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `amount` | string (decimal) | Сумма долга |
| `paid_amount` | string (decimal) | Погашено |
| `due_date` | string (date) | Срок оплаты |
| `status` | enum: `open` \| `partially_paid` \| `closed` \| `overdue` |  |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/debts/{id}/pay/`

**Погасить долг**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `amount` | string (decimal) | да |  |
| `payment_method` | enum: `cash` \| `card` \| `bank_transfer` \| `qr` \| `pos` \| `online` | да | * `cash` - Наличные
* `card` - Карта
* `bank_transfer` - Банковский перевод
* `qr` - QR-оплата
* `pos` - POS-терминал
* `online` - Онлайн |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `amount` | string (decimal) | Сумма долга |
| `paid_amount` | string (decimal) | Погашено |
| `due_date` | string (date) | Срок оплаты |
| `status` | enum: `open` \| `partially_paid` \| `closed` \| `overdue` |  |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/financial-reports/`

**Список: Финансовые отчёты**

Возвращает страницу списка «Финансовые отчёты». Поддерживает `?page=`, `?page_size=`, `?search=`, `?ordering=` и фильтры (см. параметры).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `period_date` | string (date) |  |
| `period_type` | string |  |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `period_type` | string | Период |
| `period_date` | string (date) | Дата периода |
| `data` | object | Показатели |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/financial-reports/{id}/`

**Детально: Финансовый отчёт**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `period_type` | string | Период |
| `period_date` | string (date) | Дата периода |
| `data` | object | Показатели |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/invoices/`

**Список: Счета**

Возвращает страницу списка «Счета». Поддерживает `?page=`, `?page_size=`, `?search=`, `?ordering=` и фильтры (см. параметры).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `order` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `cancelled` \| `draft` \| `issued` \| `paid` | * `draft` - Черновик
* `issued` - Выставлен
* `paid` - Оплачен
* `cancelled` - Отменён |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `invoice_number` | string | Номер |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `payment` | string (uuid) | Платёж |
| `amount` | string (decimal) | Сумма |
| `vat_percent` | string (decimal) | НДС, % |
| `issued_at` | string (date-time) | Выставлен |
| `due_date` | string (date) | Срок оплаты |
| `status` | enum: `draft` \| `issued` \| `paid` \| `cancelled` |  |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/invoices/{id}/`

**Детально: Счёт**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `invoice_number` | string | Номер |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `payment` | string (uuid) | Платёж |
| `amount` | string (decimal) | Сумма |
| `vat_percent` | string (decimal) | НДС, % |
| `issued_at` | string (date-time) | Выставлен |
| `due_date` | string (date) | Срок оплаты |
| `status` | enum: `draft` \| `issued` \| `paid` \| `cancelled` |  |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/payments/`

**Список: Платежи**

Платежи: создаются через POST /orders/{id}/pay; удаление запрещено.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `order` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `payment_method` | enum: `bank_transfer` \| `card` \| `cash` \| `online` \| `pos` \| `qr` | * `cash` - Наличные
* `card` - Карта
* `bank_transfer` - Банковский перевод
* `qr` - QR-оплата
* `pos` - POS-терминал
* `online` - Онлайн |
| `search` | string | A search term. |
| `status` | enum: `cancelled` \| `failed` \| `paid` \| `pending` \| `refunded` | * `pending` - Ожидает
* `paid` - Оплачен
* `failed` - Ошибка
* `cancelled` - Отменён
* `refunded` - Возвращён |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `payment_number` | string | Номер |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `amount` | string (decimal) | Сумма |
| `currency` | string | Валюта |
| `payment_method` | enum: `cash` \| `card` \| `bank_transfer` \| `qr` \| `pos` \| `online` |  |
| `transaction_id` | string | Внешний ID транзакции |
| `paid_by` | string (uuid) | Плательщик |
| `paid_at` | string (date-time) | Оплачен |
| `status` | enum: `pending` \| `paid` \| `failed` \| `cancelled` \| `refunded` |  |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/payments/{id}/`

**Детально: Платёж**

Платежи: создаются через POST /orders/{id}/pay; удаление запрещено.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `payment_number` | string | Номер |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `amount` | string (decimal) | Сумма |
| `currency` | string | Валюта |
| `payment_method` | enum: `cash` \| `card` \| `bank_transfer` \| `qr` \| `pos` \| `online` |  |
| `transaction_id` | string | Внешний ID транзакции |
| `paid_by` | string (uuid) | Плательщик |
| `paid_at` | string (date-time) | Оплачен |
| `status` | enum: `pending` \| `paid` \| `failed` \| `cancelled` \| `refunded` |  |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/payments/{id}/refund/`

**Возврат платежа**

Платежи: создаются через POST /orders/{id}/pay; удаление запрещено.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `amount` | string (decimal) | да |  |
| `reason` | enum: `customer_request` \| `cancelled_order` \| `wrong_payment` \| `duplicate_payment` \| `other` | да | * `customer_request` - Запрос клиента
* `cancelled_order` - Отмена заказа
* `wrong_payment` - Ошибочный платёж
* `duplicate_payment` - Дубль платежа
* `other` - Другое |
| `comment` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `payment` | string (uuid) | Платёж |
| `amount` | string (decimal) | Сумма |
| `reason` | enum: `customer_request` \| `cancelled_order` \| `wrong_payment` \| `duplicate_payment` \| `other` |  |
| `comment` | string | Комментарий |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |


---

## gps

GPS-мониторинг: координаты водителей, онлайн-карта, история, геозоны

### `GET /api/v1/geofences/`

**Список: Геозоны**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `type` | enum: `branch` \| `checkpoint` \| `custom` \| `delivery` \| `warehouse` | * `warehouse` - Склад
* `branch` - Филиал
* `checkpoint` - Контрольная точка
* `delivery` - Зона доставки
* `custom` - Произвольная |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `type` | enum: `warehouse` \| `branch` \| `checkpoint` \| `delivery` \| `custom` |  |
| `latitude` | string (decimal) | Широта центра |
| `longitude` | string (decimal) | Долгота центра |
| `radius_m` | integer (int64) | Радиус, м |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/geofences/`

**Создание: Геозона**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название |
| `type` | enum: `warehouse` \| `branch` \| `checkpoint` \| `delivery` \| `custom` | нет | * `warehouse` - Склад
* `branch` - Филиал
* `checkpoint` - Контрольная точка
* `delivery` - Зона доставки
* `custom` - Произвольная |
| `latitude` | string (decimal) | да | Широта центра |
| `longitude` | string (decimal) | да | Долгота центра |
| `radius_m` | integer (int64) | нет | Радиус, м |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `type` | enum: `warehouse` \| `branch` \| `checkpoint` \| `delivery` \| `custom` |  |
| `latitude` | string (decimal) | Широта центра |
| `longitude` | string (decimal) | Долгота центра |
| `radius_m` | integer (int64) | Радиус, м |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/geofences/{id}/`

**Детально: Геозона**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `type` | enum: `warehouse` \| `branch` \| `checkpoint` \| `delivery` \| `custom` |  |
| `latitude` | string (decimal) | Широта центра |
| `longitude` | string (decimal) | Долгота центра |
| `radius_m` | integer (int64) | Радиус, м |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/geofences/{id}/`

**Изменение: Геозона**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название |
| `type` | enum: `warehouse` \| `branch` \| `checkpoint` \| `delivery` \| `custom` | нет | * `warehouse` - Склад
* `branch` - Филиал
* `checkpoint` - Контрольная точка
* `delivery` - Зона доставки
* `custom` - Произвольная |
| `latitude` | string (decimal) | нет | Широта центра |
| `longitude` | string (decimal) | нет | Долгота центра |
| `radius_m` | integer (int64) | нет | Радиус, м |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `type` | enum: `warehouse` \| `branch` \| `checkpoint` \| `delivery` \| `custom` |  |
| `latitude` | string (decimal) | Широта центра |
| `longitude` | string (decimal) | Долгота центра |
| `radius_m` | integer (int64) | Радиус, м |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/geofences/{id}/`

**Удаление (soft delete): Геозона**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/gps/events/`

**GPS-события**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle` | string (uuid) | Автомобиль |
| `shipment` | string (uuid) | Рейс |
| `type` | enum: `stop` \| `long_stop` \| `enter_geofence` \| `exit_geofence` \| `route_deviation` \| `overspeed` \| `offline` |  |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `details` | object | Детали |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/gps/history/`

**История движения**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle` | string (uuid) | Автомобиль |
| `driver` | string (uuid) | Водитель |
| `shipment` | string (uuid) | Рейс |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `altitude` | string (decimal) | Высота, м |
| `speed` | string (decimal) | Скорость, км/ч |
| `heading` | integer | Курс, ° |
| `accuracy` | string (decimal) | Погрешность, м |
| `battery_level` | integer | Заряд, % |
| `device_time` | string (date-time) | Время устройства |
| `server_time` | string (date-time) | Время сервера |

### `GET /api/v1/gps/live/`

**Онлайн-точки автомобилей**

Онлайн-карта: последние точки машин в активных рейсах (ТЗ, раздел 10).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `vehicle_id` | string |  |
| `shipment_id` | string |  |
| `shipment_number` | string |  |
| `latitude` | string |  |
| `longitude` | string |  |
| `speed` | string |  |
| `heading` | integer |  |
| `eta_minutes` | integer |  |
| `updated_at` | string |  |

### `POST /api/v1/gps/update/`

**Отправка координат водителем**

Водитель отправляет координаты (ТЗ, разделы 03, 10). Лимит 1/5 сек.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `lat` | string (decimal) | да |  |
| `lng` | string (decimal) | да |  |
| `speed` | string (decimal) | нет |  |
| `heading` | integer | нет |  |
| `altitude` | string (decimal) | нет |  |
| `accuracy` | string (decimal) | нет |  |
| `battery_level` | integer | нет |  |
| `device_time` | string (date-time) | да |  |
| `device_id` | string | нет |  |
| `app_version` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle` | string (uuid) | Автомобиль |
| `driver` | string (uuid) | Водитель |
| `shipment` | string (uuid) | Рейс |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `altitude` | string (decimal) | Высота, м |
| `speed` | string (decimal) | Скорость, км/ч |
| `heading` | integer | Курс, ° |
| `accuracy` | string (decimal) | Погрешность, м |
| `battery_level` | integer | Заряд, % |
| `device_time` | string (date-time) | Время устройства |
| `server_time` | string (date-time) | Время сервера |


---

## health

Проверки живости сервиса и зависимостей

### `GET /api/v1/health/`

**Получение данных**

Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `status` | string |  |
| `component` | string |  |

### `GET /api/v1/health/cache/`

**Получение данных**

Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `status` | string |  |
| `component` | string |  |

### `GET /api/v1/health/celery/`

**Получение данных**

Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `status` | string |  |
| `component` | string |  |

### `GET /api/v1/health/db/`

**Получение данных**

Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `status` | string |  |
| `component` | string |  |

### `GET /api/v1/health/redis/`

**Получение данных**

Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `status` | string |  |
| `component` | string |  |

### `GET /api/v1/health/storage/`

**Получение данных**

Health-проверки (ТЗ, разделы 05, 27). Не требуют авторизации.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `status` | string |  |
| `component` | string |  |


---

## notifications

Уведомления и шаблоны

### `GET /api/v1/notification-templates/`

**Список: Шаблоны уведомлений**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `language` | enum: `en` \| `ky` \| `ru` | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `type` | enum: `email` \| `in_app` \| `push` \| `sms` \| `telegram` | * `push` - Push
* `sms` - SMS
* `email` - Email
* `telegram` - Telegram
* `in_app` - In-App |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название (ключ события) |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `title` | string | Заголовок |
| `body` | string | Шаблон текста |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/notification-templates/`

**Создание: Шаблон уведомления**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название (ключ события) |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` | да | * `push` - Push
* `sms` - SMS
* `email` - Email
* `telegram` - Telegram
* `in_app` - In-App |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `title` | string | да | Заголовок |
| `body` | string | да | Шаблон текста |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название (ключ события) |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `title` | string | Заголовок |
| `body` | string | Шаблон текста |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/notification-templates/{id}/`

**Детально: Шаблон уведомления**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название (ключ события) |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `title` | string | Заголовок |
| `body` | string | Шаблон текста |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/notification-templates/{id}/`

**Изменение: Шаблон уведомления**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название (ключ события) |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` | нет | * `push` - Push
* `sms` - SMS
* `email` - Email
* `telegram` - Telegram
* `in_app` - In-App |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `title` | string | нет | Заголовок |
| `body` | string | нет | Шаблон текста |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название (ключ события) |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `title` | string | Заголовок |
| `body` | string | Шаблон текста |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/notification-templates/{id}/`

**Удаление (soft delete): Шаблон уведомления**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/notifications/`

**Список: Уведомления**

Свои уведомления (ТЗ, раздел 03): список, отметка о прочтении.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_read` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `cancelled` \| `delivered` \| `failed` \| `pending` \| `queued` \| `read` \| `sending` \| `sent` | * `pending` - Ожидает
* `queued` - В очереди
* `sending` - Отправляется
* `sent` - Отправлено
* `delivered` - Доставлено
* `read` - Прочитано
* `failed` - Ошибка
* `cancelled` - Отменено |
| `type` | enum: `email` \| `in_app` \| `push` \| `sms` \| `telegram` | * `push` - Push
* `sms` - SMS
* `email` - Email
* `telegram` - Telegram
* `in_app` - In-App |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `title` | string | Заголовок |
| `body` | string | Текст |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `priority` | enum: `low` \| `normal` \| `high` \| `critical` |  |
| `status` | enum: `pending` \| `queued` \| `sending` \| `sent` \| `delivered` \| `read` \| `failed` \| `cancelled` |  |
| `event_type` | string | Событие-источник |
| `is_read` | boolean | Прочитано |
| `sent_at` | string (date-time) | Отправлено |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/notifications/send/`

**Отправить уведомление пользователю**

Свои уведомления (ТЗ, раздел 03): список, отметка о прочтении.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `user` | string (uuid) | да |  |
| `title` | string | да |  |
| `body` | string | да |  |
| `priority` | enum: `low` \| `normal` \| `high` \| `critical` | нет | * `low` - Низкий
* `normal` - Обычный
* `high` - Высокий
* `critical` - Критический |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `title` | string | Заголовок |
| `body` | string | Текст |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `priority` | enum: `low` \| `normal` \| `high` \| `critical` |  |
| `status` | enum: `pending` \| `queued` \| `sending` \| `sent` \| `delivered` \| `read` \| `failed` \| `cancelled` |  |
| `event_type` | string | Событие-источник |
| `is_read` | boolean | Прочитано |
| `sent_at` | string (date-time) | Отправлено |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/notifications/{id}/`

**Детально: Уведомление**

Свои уведомления (ТЗ, раздел 03): список, отметка о прочтении.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `title` | string | Заголовок |
| `body` | string | Текст |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `priority` | enum: `low` \| `normal` \| `high` \| `critical` |  |
| `status` | enum: `pending` \| `queued` \| `sending` \| `sent` \| `delivered` \| `read` \| `failed` \| `cancelled` |  |
| `event_type` | string | Событие-источник |
| `is_read` | boolean | Прочитано |
| `sent_at` | string (date-time) | Отправлено |
| `created_at` | string (date-time) | Создано |

### `PATCH /api/v1/notifications/{id}/read/`

**Отметить прочитанным**

Свои уведомления (ТЗ, раздел 03): список, отметка о прочтении.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `title` | string | Заголовок |
| `body` | string | Текст |
| `type` | enum: `push` \| `sms` \| `email` \| `telegram` \| `in_app` |  |
| `priority` | enum: `low` \| `normal` \| `high` \| `critical` |  |
| `status` | enum: `pending` \| `queued` \| `sending` \| `sent` \| `delivered` \| `read` \| `failed` \| `cancelled` |  |
| `event_type` | string | Событие-источник |
| `is_read` | boolean | Прочитано |
| `sent_at` | string (date-time) | Отправлено |
| `created_at` | string (date-time) | Создано |


---

## orders

Заказы: создание, подтверждение, оплата, статусы (FSM), история

### `GET /api/v1/orders/`

**Список: Заказы**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `client` | string (uuid) |  |
| `date_from` | string (date) |  |
| `date_to` | string (date) |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` | * `branch_pickup` - Выдача в филиале
* `door_delivery` - Доставка до двери |
| `from_branch` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `payment_type` | enum: `bank_transfer` \| `card` \| `cash` \| `post_payment` \| `qr` | * `cash` - Наличные
* `card` - Карта
* `qr` - QR-оплата
* `bank_transfer` - Банковский перевод
* `post_payment` - Постоплата |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `confirmed` \| `damaged` \| `delivered` \| `draft` \| `in_transit` \| `in_warehouse` \| `loaded` \| `lost` \| `need_correction` \| `paid` \| `partially_paid` \| `ready_for_pickup` \| `received` \| `returned` \| `waiting_confirmation` \| `waiting_payment` \| `waiting_receive` \| `waiting_shipment` | * `draft` - Черновик
* `waiting_confirmation` - Ожидает подтверждения
* `need_correction` - Требует исправления
* `confirmed` - Подтверждён
* `waiting_payment` - Ожидает оплаты
* `partially_paid` - Частично оплачен
* `paid` - Оплачен
* `waiting_receive` - Ожидает приёма груза
* `received` - Груз принят
* `in_warehouse` - На складе
* `waiting_shipment` - Ожидает рейса
* `loaded` - Погружен
* `in_transit` - В пути
* `arrived` - Прибыл
* `ready_for_pickup` - Готов к выдаче
* `delivered` - Выдан получателю
* `completed` - Завершён
* `cancelled` - Отменён
* `returned` - Возврат
* `damaged` - Повреждён
* `lost` - Утерян |
| `to_branch` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `POST /api/v1/orders/`

**Создание заказа (клиент или оператор)**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `client` | string (uuid) | нет |  |
| `sender_name` | string | да |  |
| `sender_phone` | string | да |  |
| `sender_address` | string | нет |  |
| `receiver_name` | string | да |  |
| `receiver_phone` | string | да |  |
| `receiver_address` | string | нет |  |
| `from_branch` | string (uuid) | да |  |
| `to_branch` | string (uuid) | да |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` | нет | * `cash` - Наличные
* `card` - Карта
* `qr` - QR-оплата
* `bank_transfer` - Банковский перевод
* `post_payment` - Постоплата |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` | нет | * `branch_pickup` - Выдача в филиале
* `door_delivery` - Доставка до двери |
| `comment` | string | нет |  |
| `packages` | array[object] | да |  |
| `services` | array[string (uuid)] | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `GET /api/v1/orders/{id}/`

**Детально: Заказ**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `PATCH /api/v1/orders/{id}/`

**Редактирование (до отправки)**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `sender_name` | string | нет |  |
| `sender_phone` | string | нет |  |
| `sender_address` | string | нет |  |
| `receiver_name` | string | нет |  |
| `receiver_phone` | string | нет |  |
| `receiver_address` | string | нет |  |
| `from_branch` | string (uuid) | нет |  |
| `to_branch` | string (uuid) | нет |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` | нет | * `cash` - Наличные
* `card` - Карта
* `qr` - QR-оплата
* `bank_transfer` - Банковский перевод
* `post_payment` - Постоплата |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` | нет | * `branch_pickup` - Выдача в филиале
* `door_delivery` - Доставка до двери |
| `comment` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `DELETE /api/v1/orders/{id}/`

**Отмена заказа (soft: статус CANCELLED)**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

### `POST /api/v1/orders/{id}/cancel/`

**Отменить заказ**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `comment` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `POST /api/v1/orders/{id}/confirm/`

**Подтвердить заказ**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `GET /api/v1/orders/{id}/history/`

**История статусов**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `client` | string (uuid) |  |
| `date_from` | string (date) |  |
| `date_to` | string (date) |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` | * `branch_pickup` - Выдача в филиале
* `door_delivery` - Доставка до двери |
| `from_branch` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `payment_type` | enum: `bank_transfer` \| `card` \| `cash` \| `post_payment` \| `qr` | * `cash` - Наличные
* `card` - Карта
* `qr` - QR-оплата
* `bank_transfer` - Банковский перевод
* `post_payment` - Постоплата |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `confirmed` \| `damaged` \| `delivered` \| `draft` \| `in_transit` \| `in_warehouse` \| `loaded` \| `lost` \| `need_correction` \| `paid` \| `partially_paid` \| `ready_for_pickup` \| `received` \| `returned` \| `waiting_confirmation` \| `waiting_payment` \| `waiting_receive` \| `waiting_shipment` | * `draft` - Черновик
* `waiting_confirmation` - Ожидает подтверждения
* `need_correction` - Требует исправления
* `confirmed` - Подтверждён
* `waiting_payment` - Ожидает оплаты
* `partially_paid` - Частично оплачен
* `paid` - Оплачен
* `waiting_receive` - Ожидает приёма груза
* `received` - Груз принят
* `in_warehouse` - На складе
* `waiting_shipment` - Ожидает рейса
* `loaded` - Погружен
* `in_transit` - В пути
* `arrived` - Прибыл
* `ready_for_pickup` - Готов к выдаче
* `delivered` - Выдан получателю
* `completed` - Завершён
* `cancelled` - Отменён
* `returned` - Возврат
* `damaged` - Повреждён
* `lost` - Утерян |
| `to_branch` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `from_status` | string | Из статуса |
| `to_status` | string | В статус |
| `changed_by` | string (uuid) | Кто изменил |
| `changed_by_name` | string |  |
| `comment` | string | Комментарий |
| `created_at` | string (date-time) | Когда |

### `POST /api/v1/orders/{id}/need-correction/`

**Вернуть на исправление**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `comment` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `POST /api/v1/orders/{id}/pay/`

**Зафиксировать оплату**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `amount` | string (decimal) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `POST /api/v1/orders/{id}/status/`

**Изменить статус (FSM)**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` | да | * `draft` - Черновик
* `waiting_confirmation` - Ожидает подтверждения
* `need_correction` - Требует исправления
* `confirmed` - Подтверждён
* `waiting_payment` - Ожидает оплаты
* `partially_paid` - Частично оплачен
* `paid` - Оплачен
* `waiting_receive` - Ожидает приёма груза
* `received` - Груз принят
* `in_warehouse` - На складе
* `waiting_shipment` - Ожидает рейса
* `loaded` - Погружен
* `in_transit` - В пути
* `arrived` - Прибыл
* `ready_for_pickup` - Готов к выдаче
* `delivered` - Выдан получателю
* `completed` - Завершён
* `cancelled` - Отменён
* `returned` - Возврат
* `damaged` - Повреждён
* `lost` - Утерян |
| `comment` | string | нет |  |
| `version` | integer | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `POST /api/v1/orders/{id}/submit/`

**Отправить на проверку**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order_number` | string | Номер заказа |
| `client` | string (uuid) | Клиент |
| `client_phone` | string |  |
| `sender_name` | string | Отправитель |
| `sender_phone` | string | Телефон отправителя |
| `sender_address` | string | Адрес отправителя |
| `receiver_name` | string | Получатель |
| `receiver_phone` | string | Телефон получателя |
| `receiver_address` | string | Адрес получателя |
| `from_branch` | string (uuid) | Филиал отправления |
| `from_branch_name` | string |  |
| `to_branch` | string (uuid) | Филиал назначения |
| `to_branch_name` | string |  |
| `payment_type` | enum: `cash` \| `card` \| `qr` \| `bank_transfer` \| `post_payment` |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` |  |
| `tariff` | string (uuid) | Тариф |
| `total_price` | string (decimal) | Стоимость |
| `insurance_price` | string (decimal) | Страховка |
| `paid_amount` | string (decimal) | Оплачено |
| `price_details` | object |  |
| `status` | enum: `draft` \| `waiting_confirmation` \| `need_correction` \| `confirmed` \| `waiting_payment` \| `partially_paid` \| `paid` \| `waiting_receive` \| `received` \| `in_warehouse` \| `waiting_shipment` \| `loaded` \| `in_transit` \| `arrived` \| `ready_for_pickup` \| `delivered` \| `completed` \| `cancelled` \| `returned` \| `damaged` \| `lost` |  |
| `comment` | string | Комментарий |
| `version` | integer | Версия |
| `active_shipment` | object |  |

### `GET /api/v1/orders/{id}/tracking/`

**Трекинг заказа**

Заказы (ТЗ, разделы 03, 07). Удаление — только Soft Delete.

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `client` | string (uuid) |  |
| `date_from` | string (date) |  |
| `date_to` | string (date) |  |
| `delivery_type` | enum: `branch_pickup` \| `door_delivery` | * `branch_pickup` - Выдача в филиале
* `door_delivery` - Доставка до двери |
| `from_branch` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `payment_type` | enum: `bank_transfer` \| `card` \| `cash` \| `post_payment` \| `qr` | * `cash` - Наличные
* `card` - Карта
* `qr` - QR-оплата
* `bank_transfer` - Банковский перевод
* `post_payment` - Постоплата |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `confirmed` \| `damaged` \| `delivered` \| `draft` \| `in_transit` \| `in_warehouse` \| `loaded` \| `lost` \| `need_correction` \| `paid` \| `partially_paid` \| `ready_for_pickup` \| `received` \| `returned` \| `waiting_confirmation` \| `waiting_payment` \| `waiting_receive` \| `waiting_shipment` | * `draft` - Черновик
* `waiting_confirmation` - Ожидает подтверждения
* `need_correction` - Требует исправления
* `confirmed` - Подтверждён
* `waiting_payment` - Ожидает оплаты
* `partially_paid` - Частично оплачен
* `paid` - Оплачен
* `waiting_receive` - Ожидает приёма груза
* `received` - Груз принят
* `in_warehouse` - На складе
* `waiting_shipment` - Ожидает рейса
* `loaded` - Погружен
* `in_transit` - В пути
* `arrived` - Прибыл
* `ready_for_pickup` - Готов к выдаче
* `delivered` - Выдан получателю
* `completed` - Завершён
* `cancelled` - Отменён
* `returned` - Возврат
* `damaged` - Повреждён
* `lost` - Утерян |
| `to_branch` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `package` | string (uuid) | Груз |
| `status` | string | Событие/статус |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `comment` | string | Комментарий |
| `employee` | string (uuid) | Сотрудник |
| `employee_name` | string |  |
| `created_at` | string (date-time) | Создано |


---

## packages

Грузовые места: QR/штрихкоды, фотофиксация, сканирование

### `GET /api/v1/packages/`

**Список: Грузовые места**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `dangerous` | boolean |  |
| `fragile` | boolean |  |
| `order` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `checked` \| `created` \| `damaged` \| `delivered` \| `in_transit` \| `loaded` \| `lost` \| `ready_for_pickup` \| `received` \| `returned` \| `stored` \| `unloaded` \| `waiting_loading` | * `created` - Создан
* `received` - Принят
* `checked` - Проверен
* `stored` - Размещён
* `waiting_loading` - Ожидает погрузки
* `loaded` - Погружен
* `in_transit` - В пути
* `unloaded` - Разгружен
* `ready_for_pickup` - Готов к выдаче
* `delivered` - Выдан
* `returned` - Возврат
* `damaged` - Повреждён
* `lost` - Утерян |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/packages/`

**Добавить грузовое место к заказу**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `title` | string | да |  |
| `description` | string | нет |  |
| `weight` | string (decimal) | да |  |
| `length` | integer | нет |  |
| `width` | integer | нет |  |
| `height` | integer | нет |  |
| `volume` | string (decimal) | нет |  |
| `declared_price` | string (decimal) | нет |  |
| `fragile` | boolean | нет |  |
| `dangerous` | boolean | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/packages/scan/`

**Сканировать QR**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/packages/{id}/`

**Детально: Грузовое место**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/packages/{id}/`

**Изменить грузовое место**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `title` | string | нет |  |
| `description` | string | нет |  |
| `weight` | string (decimal) | нет |  |
| `length` | integer | нет |  |
| `width` | integer | нет |  |
| `height` | integer | нет |  |
| `volume` | string (decimal) | нет |  |
| `declared_price` | string (decimal) | нет |  |
| `fragile` | boolean | нет |  |
| `dangerous` | boolean | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/packages/{id}/`

**Удалить грузовое место (soft)**

Грузовые места (ТЗ, раздел 03: PACKAGES).

### `POST /api/v1/packages/{id}/generate-qr/`

**Сгенерировать QR (один раз)**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/packages/{id}/upload-photo/`

**Загрузить фото груза**

Грузовые места (ТЗ, раздел 03: PACKAGES).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `image` | string (binary) | да |  |
| `type` | enum: `receiving` \| `loading` \| `unloading` \| `delivery` \| `damage` | да | * `receiving` - Приём
* `loading` - Погрузка
* `unloading` - Разгрузка
* `delivery` - Выдача
* `damage` - Повреждение |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `package` | string (uuid) | Груз |
| `image` | string (uri) | Фото |
| `type` | enum: `receiving` \| `loading` \| `unloading` \| `delivery` \| `damage` |  |
| `uploaded_by` | string (uuid) | Загрузил |
| `created_at` | string (date-time) | Создано |


---

## reports

Аналитические отчёты

### `GET /api/v1/reports/drivers/`

**Получение данных**

### `GET /api/v1/reports/finance/`

**Получение данных**

### `GET /api/v1/reports/orders/`

**Получение данных**

### `GET /api/v1/reports/warehouse/`

**Получение данных**


---

## routes

Маршруты между филиалами

### `GET /api/v1/route-points/`

**Список: Точки маршрута**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `city` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `route` | string (uuid) |  |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `route` | string (uuid) | Маршрут |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `sequence` | integer (int64) | Порядок |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/route-points/`

**Создание: Точка маршрута**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `route` | string (uuid) | да | Маршрут |
| `city` | string (uuid) | да | Город |
| `sequence` | integer (int64) | да | Порядок |
| `latitude` | string (decimal) | нет | Широта |
| `longitude` | string (decimal) | нет | Долгота |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `route` | string (uuid) | Маршрут |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `sequence` | integer (int64) | Порядок |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |

### `GET /api/v1/route-points/{id}/`

**Детально: Точка маршрута**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `route` | string (uuid) | Маршрут |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `sequence` | integer (int64) | Порядок |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |

### `PATCH /api/v1/route-points/{id}/`

**Изменение: Точка маршрута**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `route` | string (uuid) | нет | Маршрут |
| `city` | string (uuid) | нет | Город |
| `sequence` | integer (int64) | нет | Порядок |
| `latitude` | string (decimal) | нет | Широта |
| `longitude` | string (decimal) | нет | Долгота |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `route` | string (uuid) | Маршрут |
| `city` | string (uuid) | Город |
| `city_name` | string |  |
| `sequence` | integer (int64) | Порядок |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |

### `DELETE /api/v1/route-points/{id}/`

**Удаление (soft delete): Точка маршрута**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/routes/`

**Список: Маршруты**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `end_branch` | string (uuid) |  |
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `start_branch` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `start_branch` | string (uuid) | Старт |
| `start_branch_name` | string |  |
| `end_branch` | string (uuid) | Финиш |
| `end_branch_name` | string |  |
| `estimated_distance` | string (decimal) | Расстояние, км |
| `estimated_duration` | integer (int64) | Время в пути, мин |
| `points` | array[object] |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/routes/`

**Создание: Маршрут**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название |
| `code` | string | да | Код |
| `start_branch` | string (uuid) | да | Старт |
| `end_branch` | string (uuid) | да | Финиш |
| `estimated_distance` | string (decimal) | да | Расстояние, км |
| `estimated_duration` | integer (int64) | да | Время в пути, мин |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `start_branch` | string (uuid) | Старт |
| `start_branch_name` | string |  |
| `end_branch` | string (uuid) | Финиш |
| `end_branch_name` | string |  |
| `estimated_distance` | string (decimal) | Расстояние, км |
| `estimated_duration` | integer (int64) | Время в пути, мин |
| `points` | array[object] |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/routes/{id}/`

**Детально: Маршрут**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `start_branch` | string (uuid) | Старт |
| `start_branch_name` | string |  |
| `end_branch` | string (uuid) | Финиш |
| `end_branch_name` | string |  |
| `estimated_distance` | string (decimal) | Расстояние, км |
| `estimated_duration` | integer (int64) | Время в пути, мин |
| `points` | array[object] |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/routes/{id}/`

**Изменение: Маршрут**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `start_branch` | string (uuid) | нет | Старт |
| `end_branch` | string (uuid) | нет | Финиш |
| `estimated_distance` | string (decimal) | нет | Расстояние, км |
| `estimated_duration` | integer (int64) | нет | Время в пути, мин |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `start_branch` | string (uuid) | Старт |
| `start_branch_name` | string |  |
| `end_branch` | string (uuid) | Финиш |
| `end_branch_name` | string |  |
| `estimated_distance` | string (decimal) | Расстояние, км |
| `estimated_duration` | integer (int64) | Время в пути, мин |
| `points` | array[object] |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/routes/{id}/`

**Удаление (soft delete): Маршрут**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}


---

## shipments

Рейсы: состав, погрузка/разгрузка по сканам, жизненный цикл, инциденты

### `GET /api/v1/shipments/`

**Список: Рейсы**

Рейсы (ТЗ, разделы 03, 09).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `arrival_branch` | string (uuid) |  |
| `departure_branch` | string (uuid) |  |
| `driver` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `draft` \| `failed` \| `gps_lost` \| `in_transit` \| `loaded` \| `loading` \| `planned` \| `ready` \| `started` \| `unloading` | * `draft` - Черновик
* `planned` - Запланирован
* `ready` - Готов к погрузке
* `loading` - Погрузка
* `loaded` - Погружен
* `started` - Стартовал
* `in_transit` - В пути
* `gps_lost` - Потеря GPS
* `arrived` - Прибыл
* `unloading` - Разгрузка
* `completed` - Завершён
* `cancelled` - Отменён
* `failed` - Сорван |
| `vehicle` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/`

**Создать рейс**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `departure_branch` | string (uuid) | да |  |
| `arrival_branch` | string (uuid) | да |  |
| `route` | string (uuid) | нет |  |
| `vehicle` | string (uuid) | нет |  |
| `driver` | string (uuid) | нет |  |
| `planned_departure` | string (date-time) | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/shipments/{id}/`

**Детально: Рейс**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/shipments/{id}/`

**Изменение: Рейс**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/shipments/{id}/`

**Отменить рейс (до старта)**

Рейсы (ТЗ, разделы 03, 09).

### `POST /api/v1/shipments/{id}/add-order/`

**Добавить заказ в рейс**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `order` | string (uuid) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/arrive/`

**Прибытие**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/assign-driver/`

**Назначить водителя**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `id` | string (uuid) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/assign-vehicle/`

**Назначить автомобиль**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `id` | string (uuid) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/finish/`

**Завершить рейс**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/shipments/{id}/history/`

**История статусов**

Рейсы (ТЗ, разделы 03, 09).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `arrival_branch` | string (uuid) |  |
| `departure_branch` | string (uuid) |  |
| `driver` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `draft` \| `failed` \| `gps_lost` \| `in_transit` \| `loaded` \| `loading` \| `planned` \| `ready` \| `started` \| `unloading` | * `draft` - Черновик
* `planned` - Запланирован
* `ready` - Готов к погрузке
* `loading` - Погрузка
* `loaded` - Погружен
* `started` - Стартовал
* `in_transit` - В пути
* `gps_lost` - Потеря GPS
* `arrived` - Прибыл
* `unloading` - Разгрузка
* `completed` - Завершён
* `cancelled` - Отменён
* `failed` - Сорван |
| `vehicle` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `from_status` | string | Из статуса |
| `to_status` | string | В статус |
| `changed_by` | string (uuid) | Кто изменил |
| `comment` | string | Комментарий |
| `created_at` | string (date-time) | Когда |

### `GET /api/v1/shipments/{id}/incidents/`

**Инциденты рейса (GET список, POST создать)**

Рейсы (ТЗ, разделы 03, 09).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `arrival_branch` | string (uuid) |  |
| `departure_branch` | string (uuid) |  |
| `driver` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `draft` \| `failed` \| `gps_lost` \| `in_transit` \| `loaded` \| `loading` \| `planned` \| `ready` \| `started` \| `unloading` | * `draft` - Черновик
* `planned` - Запланирован
* `ready` - Готов к погрузке
* `loading` - Погрузка
* `loaded` - Погружен
* `started` - Стартовал
* `in_transit` - В пути
* `gps_lost` - Потеря GPS
* `arrived` - Прибыл
* `unloading` - Разгрузка
* `completed` - Завершён
* `cancelled` - Отменён
* `failed` - Сорван |
| `vehicle` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment` | string (uuid) | Рейс |
| `type` | enum: `accident` \| `breakdown` \| `delay` \| `traffic` \| `weather` \| `damage` \| `loss` \| `other` |  |
| `description` | string | Описание |
| `photo` | string (uri) | Фото |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/shipments/{id}/incidents/`

**Инциденты рейса (GET список, POST создать)**

Рейсы (ТЗ, разделы 03, 09).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `arrival_branch` | string (uuid) |  |
| `departure_branch` | string (uuid) |  |
| `driver` | string (uuid) |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `arrived` \| `cancelled` \| `completed` \| `draft` \| `failed` \| `gps_lost` \| `in_transit` \| `loaded` \| `loading` \| `planned` \| `ready` \| `started` \| `unloading` | * `draft` - Черновик
* `planned` - Запланирован
* `ready` - Готов к погрузке
* `loading` - Погрузка
* `loaded` - Погружен
* `started` - Стартовал
* `in_transit` - В пути
* `gps_lost` - Потеря GPS
* `arrived` - Прибыл
* `unloading` - Разгрузка
* `completed` - Завершён
* `cancelled` - Отменён
* `failed` - Сорван |
| `vehicle` | string (uuid) |  |

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `type` | enum: `accident` \| `breakdown` \| `delay` \| `traffic` \| `weather` \| `damage` \| `loss` \| `other` | да | * `accident` - ДТП
* `breakdown` - Поломка
* `delay` - Задержка
* `traffic` - Пробка
* `weather` - Плохая погода
* `damage` - Повреждение груза
* `loss` - Потеря груза
* `other` - Другое |
| `description` | string | да |  |
| `latitude` | string (decimal) | нет |  |
| `longitude` | string (decimal) | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment` | string (uuid) | Рейс |
| `type` | enum: `accident` \| `breakdown` \| `delay` \| `traffic` \| `weather` \| `damage` \| `loss` \| `other` |  |
| `description` | string | Описание |
| `photo` | string (uri) | Фото |
| `latitude` | string (decimal) | Широта |
| `longitude` | string (decimal) | Долгота |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/shipments/{id}/load-package/`

**Скан груза при погрузке**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/loaded/`

**Погрузка завершена**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/loading/`

**Начать погрузку**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/plan/`

**Запланировать**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/ready/`

**Готов к погрузке**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/remove-order/`

**Убрать заказ из рейса**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `order` | string (uuid) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/start/`

**Старт рейса (чек-лист)**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/unload-package/`

**Скан груза при разгрузке**

Рейсы (ТЗ, разделы 03, 09).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/shipments/{id}/unloading/`

**Начать разгрузку**

Рейсы (ТЗ, разделы 03, 09).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `shipment_number` | string | Номер рейса |
| `vehicle` | string (uuid) | Автомобиль |
| `vehicle_plate` | string |  |
| `driver` | string (uuid) | Водитель |
| `driver_name` | string |  |
| `route` | string (uuid) | Маршрут |
| `route_code` | string |  |
| `departure_branch` | string (uuid) | Филиал отправления |
| `departure_branch_name` | string |  |
| `arrival_branch` | string (uuid) | Филиал прибытия |
| `arrival_branch_name` | string |  |
| `planned_departure` | string (date-time) | План отправления |
| `departure_time` | string (date-time) | Фактическое отправление |
| `arrival_time` | string (date-time) | Фактическое прибытие |
| `status` | enum: `draft` \| `planned` \| `ready` \| `loading` \| `loaded` \| `started` \| `in_transit` \| `gps_lost` \| `arrived` \| `unloading` \| `completed` \| `cancelled` \| `failed` |  |
| `version` | integer | Версия |
| `items` | array[object] |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |


---

## tariffs

Тарифы, дополнительные услуги, калькулятор стоимости

### `GET /api/v1/additional-services/`

**Список: Дополнительные услуги**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `price` | string (decimal) | Цена |
| `description` | string | Описание |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/additional-services/`

**Создание: Дополнительная услуга**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название |
| `code` | string | да | Код |
| `price` | string (decimal) | да | Цена |
| `description` | string | нет | Описание |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `price` | string (decimal) | Цена |
| `description` | string | Описание |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/additional-services/{id}/`

**Детально: Дополнительная услуга**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `price` | string (decimal) | Цена |
| `description` | string | Описание |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/additional-services/{id}/`

**Изменение: Дополнительная услуга**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `price` | string (decimal) | нет | Цена |
| `description` | string | нет | Описание |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `price` | string (decimal) | Цена |
| `description` | string | Описание |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/additional-services/{id}/`

**Удаление (soft delete): Дополнительная услуга**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/tariffs/`

**Список: Тарифы**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `from_city` | string (uuid) |  |
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `to_city` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `from_city` | string (uuid) | Откуда |
| `from_city_name` | string |  |
| `to_city` | string (uuid) | Куда |
| `to_city_name` | string |  |
| `base_price` | string (decimal) | Базовая цена |
| `price_per_kg` | string (decimal) | Цена за кг |
| `price_per_m3` | string (decimal) | Цена за м³ |
| `min_price` | string (decimal) | Минимальная стоимость |
| `insurance_percent` | string (decimal) | Страховка, % от объявленной ценности |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/tariffs/`

**Создание: Тариф**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название |
| `code` | string | да | Код |
| `from_city` | string (uuid) | нет | Откуда |
| `to_city` | string (uuid) | нет | Куда |
| `base_price` | string (decimal) | да | Базовая цена |
| `price_per_kg` | string (decimal) | нет | Цена за кг |
| `price_per_m3` | string (decimal) | нет | Цена за м³ |
| `min_price` | string (decimal) | нет | Минимальная стоимость |
| `insurance_percent` | string (decimal) | нет | Страховка, % от объявленной ценности |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `from_city` | string (uuid) | Откуда |
| `from_city_name` | string |  |
| `to_city` | string (uuid) | Куда |
| `to_city_name` | string |  |
| `base_price` | string (decimal) | Базовая цена |
| `price_per_kg` | string (decimal) | Цена за кг |
| `price_per_m3` | string (decimal) | Цена за м³ |
| `min_price` | string (decimal) | Минимальная стоимость |
| `insurance_percent` | string (decimal) | Страховка, % от объявленной ценности |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/tariffs/calculate/`

**Расчёт стоимости доставки**

Калькулятор стоимости доставки — доступен всем авторизованным,
включая клиентов (ТЗ, раздел 15: расчёт стоимости в Client App).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `from_city` | string (uuid) | да |  |
| `to_city` | string (uuid) | да |  |
| `weight` | string (decimal) | да |  |
| `volume` | string (decimal) | нет |  |
| `declared_value` | string (decimal) | нет |  |
| `services` | array[string (uuid)] | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `tariff_code` | string |  |
| `base_price` | string (decimal) |  |
| `weight_price` | string (decimal) |  |
| `volume_price` | string (decimal) |  |
| `services_price` | string (decimal) |  |
| `insurance_price` | string (decimal) |  |
| `total_price` | string (decimal) |  |

### `GET /api/v1/tariffs/{id}/`

**Детально: Тариф**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `from_city` | string (uuid) | Откуда |
| `from_city_name` | string |  |
| `to_city` | string (uuid) | Куда |
| `to_city_name` | string |  |
| `base_price` | string (decimal) | Базовая цена |
| `price_per_kg` | string (decimal) | Цена за кг |
| `price_per_m3` | string (decimal) | Цена за м³ |
| `min_price` | string (decimal) | Минимальная стоимость |
| `insurance_percent` | string (decimal) | Страховка, % от объявленной ценности |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/tariffs/{id}/`

**Изменение: Тариф**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `from_city` | string (uuid) | нет | Откуда |
| `to_city` | string (uuid) | нет | Куда |
| `base_price` | string (decimal) | нет | Базовая цена |
| `price_per_kg` | string (decimal) | нет | Цена за кг |
| `price_per_m3` | string (decimal) | нет | Цена за м³ |
| `min_price` | string (decimal) | нет | Минимальная стоимость |
| `insurance_percent` | string (decimal) | нет | Страховка, % от объявленной ценности |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `from_city` | string (uuid) | Откуда |
| `from_city_name` | string |  |
| `to_city` | string (uuid) | Куда |
| `to_city_name` | string |  |
| `base_price` | string (decimal) | Базовая цена |
| `price_per_kg` | string (decimal) | Цена за кг |
| `price_per_m3` | string (decimal) | Цена за м³ |
| `min_price` | string (decimal) | Минимальная стоимость |
| `insurance_percent` | string (decimal) | Страховка, % от объявленной ценности |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/tariffs/{id}/`

**Удаление (soft delete): Тариф**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}


---

## users

Управление пользователями (SuperAdmin/Director)

### `GET /api/v1/users/`

**Список: Пользователи**

Управление пользователями (матрица прав — ТЗ, раздел 14).

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `date_from` | string (date) |  |
| `date_to` | string (date) |  |
| `is_active` | boolean |  |
| `is_verified` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `role` | enum: `client` \| `director` \| `driver` \| `finance` \| `operator` \| `superadmin` \| `warehouse` | * `client` - Клиент
* `operator` - Оператор
* `warehouse` - Сотрудник склада
* `driver` - Водитель
* `finance` - Финансист
* `director` - Директор
* `superadmin` - Суперадминистратор |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `POST /api/v1/users/`

**Создание пользователя**

Управление пользователями (матрица прав — ТЗ, раздел 14).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | да |  |
| `email` | string (email) | нет |  |
| `username` | string | нет |  |
| `last_name` | string | нет |  |
| `first_name` | string | нет |  |
| `middle_name` | string | нет |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` | да | * `client` - Клиент
* `operator` - Оператор
* `warehouse` - Сотрудник склада
* `driver` - Водитель
* `finance` - Финансист
* `director` - Директор
* `superadmin` - Суперадминистратор |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `timezone` | string | нет |  |
| `is_active` | boolean | нет |  |
| `is_verified` | boolean | нет |  |
| `company_name` | string | нет |  |
| `passport_number` | string | нет |  |
| `address` | string | нет |  |
| `notes` | string | нет |  |
| `discount_percent` | string (decimal) | нет |  |
| `branch` | string (uuid) | нет |  |
| `department` | string | нет |  |
| `position` | string | нет |  |
| `hired_at` | string (date) | нет |  |
| `salary` | string (decimal) | нет |  |
| `driver_license` | string | нет |  |
| `license_expiry_date` | string (date) | нет |  |
| `medical_certificate` | string | нет |  |
| `experience_years` | integer | нет |  |
| `password` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `GET /api/v1/users/{id}/`

**Детально: Пользователь**

Управление пользователями (матрица прав — ТЗ, раздел 14).

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `PATCH /api/v1/users/{id}/`

**Изменение пользователя**

Управление пользователями (матрица прав — ТЗ, раздел 14).

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `phone` | string | нет |  |
| `email` | string (email) | нет |  |
| `username` | string | нет |  |
| `last_name` | string | нет |  |
| `first_name` | string | нет |  |
| `middle_name` | string | нет |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` | нет | * `client` - Клиент
* `operator` - Оператор
* `warehouse` - Сотрудник склада
* `driver` - Водитель
* `finance` - Финансист
* `director` - Директор
* `superadmin` - Суперадминистратор |
| `language` | enum: `ky` \| `ru` \| `en` | нет | * `ky` - Кыргызча
* `ru` - Русский
* `en` - English |
| `timezone` | string | нет |  |
| `is_active` | boolean | нет |  |
| `is_verified` | boolean | нет |  |
| `company_name` | string | нет |  |
| `passport_number` | string | нет |  |
| `address` | string | нет |  |
| `notes` | string | нет |  |
| `discount_percent` | string (decimal) | нет |  |
| `branch` | string (uuid) | нет |  |
| `department` | string | нет |  |
| `position` | string | нет |  |
| `hired_at` | string (date) | нет |  |
| `salary` | string (decimal) | нет |  |
| `driver_license` | string | нет |  |
| `license_expiry_date` | string (date) | нет |  |
| `medical_certificate` | string | нет |  |
| `experience_years` | integer | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `phone` | string | Телефон |
| `email` | string (email) |  |
| `username` | string | Логин |
| `last_name` | string | Фамилия |
| `first_name` | string | Имя |
| `middle_name` | string | Отчество |
| `full_name` | string |  |
| `role` | enum: `client` \| `operator` \| `warehouse` \| `driver` \| `finance` \| `director` \| `superadmin` |  |
| `avatar` | string (uri) | Аватар |
| `language` | enum: `ky` \| `ru` \| `en` |  |
| `timezone` | string | Часовой пояс |
| `is_verified` | boolean | Подтверждён |
| `is_active` | boolean | Активен |
| `last_login` | string (date-time) | Последний вход |
| `created_at` | string (date-time) | Создано |
| `profile` | object |  |

### `DELETE /api/v1/users/{id}/`

**Удаление пользователя (soft delete)**

Управление пользователями (матрица прав — ТЗ, раздел 14).


---

## vehicles

Автопарк и назначение водителей

### `GET /api/v1/vehicle-types/`

**Список: Типы автомобилей**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `axle_count` | integer (int64) | Количество осей |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/vehicle-types/`

**Создание: Тип автомобиля**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | да | Название |
| `code` | string | да | Код |
| `max_weight` | string (decimal) | да | Макс. вес, кг |
| `max_volume` | string (decimal) | да | Макс. объём, м³ |
| `axle_count` | integer (int64) | нет | Количество осей |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `axle_count` | integer (int64) | Количество осей |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/vehicle-types/{id}/`

**Детально: Тип автомобиля**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `axle_count` | integer (int64) | Количество осей |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/vehicle-types/{id}/`

**Изменение: Тип автомобиля**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `max_weight` | string (decimal) | нет | Макс. вес, кг |
| `max_volume` | string (decimal) | нет | Макс. объём, м³ |
| `axle_count` | integer (int64) | нет | Количество осей |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `name` | string | Название |
| `code` | string | Код |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `axle_count` | integer (int64) | Количество осей |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/vehicle-types/{id}/`

**Удаление (soft delete): Тип автомобиля**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/vehicles/`

**Список: Автомобили**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `fuel_type` | enum: `diesel` \| `electric` \| `gas` \| `hybrid` \| `petrol` | * `petrol` - Бензин
* `diesel` - Дизель
* `gas` - Газ
* `electric` - Электро
* `hybrid` - Гибрид |
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `status` | enum: `available` \| `busy` \| `inactive` \| `maintenance` | * `available` - Свободен
* `busy` - В рейсе
* `maintenance` - На обслуживании
* `inactive` - Не используется |
| `vehicle_type` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle_type` | string (uuid) | Тип |
| `vehicle_type_name` | string |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `plate_number` | string | Госномер |
| `vin` | string |  |
| `brand` | string | Марка |
| `model` | string | Модель |
| `year` | integer (int64) | Год выпуска |
| `color` | string | Цвет |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` |  |
| `mileage` | integer (int64) | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` |  |
| `current_driver` | string (uuid) | Текущий водитель |
| `driver_phone` | string |  |
| `driver_name` | string |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/vehicles/`

**Создание: Автомобиль**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `vehicle_type` | string (uuid) | да | Тип |
| `branch` | string (uuid) | нет | Филиал |
| `plate_number` | string | да | Госномер |
| `vin` | string | нет |  |
| `brand` | string | да | Марка |
| `model` | string | нет | Модель |
| `year` | integer (int64) | нет | Год выпуска |
| `color` | string | нет | Цвет |
| `max_weight` | string (decimal) | да | Макс. вес, кг |
| `max_volume` | string (decimal) | да | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` | нет | * `petrol` - Бензин
* `diesel` - Дизель
* `gas` - Газ
* `electric` - Электро
* `hybrid` - Гибрид |
| `mileage` | integer (int64) | нет | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` | нет | * `available` - Свободен
* `busy` - В рейсе
* `maintenance` - На обслуживании
* `inactive` - Не используется |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle_type` | string (uuid) | Тип |
| `vehicle_type_name` | string |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `plate_number` | string | Госномер |
| `vin` | string |  |
| `brand` | string | Марка |
| `model` | string | Модель |
| `year` | integer (int64) | Год выпуска |
| `color` | string | Цвет |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` |  |
| `mileage` | integer (int64) | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` |  |
| `current_driver` | string (uuid) | Текущий водитель |
| `driver_phone` | string |  |
| `driver_name` | string |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/vehicles/{id}/`

**Детально: Автомобиль**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle_type` | string (uuid) | Тип |
| `vehicle_type_name` | string |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `plate_number` | string | Госномер |
| `vin` | string |  |
| `brand` | string | Марка |
| `model` | string | Модель |
| `year` | integer (int64) | Год выпуска |
| `color` | string | Цвет |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` |  |
| `mileage` | integer (int64) | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` |  |
| `current_driver` | string (uuid) | Текущий водитель |
| `driver_phone` | string |  |
| `driver_name` | string |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/vehicles/{id}/`

**Изменение: Автомобиль**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `vehicle_type` | string (uuid) | нет | Тип |
| `branch` | string (uuid) | нет | Филиал |
| `plate_number` | string | нет | Госномер |
| `vin` | string | нет |  |
| `brand` | string | нет | Марка |
| `model` | string | нет | Модель |
| `year` | integer (int64) | нет | Год выпуска |
| `color` | string | нет | Цвет |
| `max_weight` | string (decimal) | нет | Макс. вес, кг |
| `max_volume` | string (decimal) | нет | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` | нет | * `petrol` - Бензин
* `diesel` - Дизель
* `gas` - Газ
* `electric` - Электро
* `hybrid` - Гибрид |
| `mileage` | integer (int64) | нет | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` | нет | * `available` - Свободен
* `busy` - В рейсе
* `maintenance` - На обслуживании
* `inactive` - Не используется |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle_type` | string (uuid) | Тип |
| `vehicle_type_name` | string |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `plate_number` | string | Госномер |
| `vin` | string |  |
| `brand` | string | Марка |
| `model` | string | Модель |
| `year` | integer (int64) | Год выпуска |
| `color` | string | Цвет |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` |  |
| `mileage` | integer (int64) | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` |  |
| `current_driver` | string (uuid) | Текущий водитель |
| `driver_phone` | string |  |
| `driver_name` | string |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/vehicles/{id}/`

**Удаление (soft delete): Автомобиль**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `POST /api/v1/vehicles/{id}/assign-driver/`

**Назначить водителя**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `driver` | string (uuid) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle_type` | string (uuid) | Тип |
| `vehicle_type_name` | string |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `plate_number` | string | Госномер |
| `vin` | string |  |
| `brand` | string | Марка |
| `model` | string | Модель |
| `year` | integer (int64) | Год выпуска |
| `color` | string | Цвет |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` |  |
| `mileage` | integer (int64) | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` |  |
| `current_driver` | string (uuid) | Текущий водитель |
| `driver_phone` | string |  |
| `driver_name` | string |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/vehicles/{id}/unassign-driver/`

**Снять водителя**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `vehicle_type` | string (uuid) | Тип |
| `vehicle_type_name` | string |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `plate_number` | string | Госномер |
| `vin` | string |  |
| `brand` | string | Марка |
| `model` | string | Модель |
| `year` | integer (int64) | Год выпуска |
| `color` | string | Цвет |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `max_volume` | string (decimal) | Макс. объём, м³ |
| `fuel_type` | enum: `petrol` \| `diesel` \| `gas` \| `electric` \| `hybrid` |  |
| `mileage` | integer (int64) | Пробег, км |
| `status` | enum: `available` \| `busy` \| `maintenance` \| `inactive` |  |
| `current_driver` | string (uuid) | Текущий водитель |
| `driver_phone` | string |  |
| `driver_name` | string |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |


---

## warehouse-operations

Складские процессы: приём, размещение, перемещение, инвентаризация, выдача

### `POST /api/v1/orders/{order_id}/issue/`

**Выдача заказа получателю**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `received_by_name` | string | да |  |
| `document_number` | string | да |  |
| `qr_codes` | array[string] | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `received_by_name` | string | Кто получил |
| `document_number` | string | Документ |
| `signature` | string (uri) | Подпись |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/warehouse-operations/check/`

**Проверить, взвесить, обмерить**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |
| `weight` | string (decimal) | нет |  |
| `length` | integer | нет |  |
| `width` | integer | нет |  |
| `height` | integer | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/warehouse-operations/damage/`

**Акт повреждения**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |
| `description` | string | да |  |
| `reason` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `package` | string (uuid) | Груз |
| `description` | string | Описание повреждения |
| `reason` | string | Причина |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/warehouse-operations/inventory/`

**Открыть инвентаризацию**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `warehouse` | string (uuid) | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `finished_at` | string (date-time) | Завершена |
| `report` | object | Отчёт |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/warehouse-operations/inventory/{session_id}/close/`

**Закрыть инвентаризацию (отчёт о расхождениях)**

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `finished_at` | string (date-time) | Завершена |
| `report` | object | Отчёт |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/warehouse-operations/inventory/{session_id}/scan/`

**Скан груза в инвентаризации**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `finished_at` | string (date-time) | Завершена |
| `report` | object | Отчёт |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/warehouse-operations/lost/`

**Акт утери**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |
| `description` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `package` | string (uuid) | Груз |
| `description` | string | Обстоятельства |
| `created_by` | string (uuid) | Создал |
| `created_at` | string (date-time) | Создано |

### `POST /api/v1/warehouse-operations/move/`

**Переместить между ячейками**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |
| `to_cell` | string (uuid) | да |  |
| `reason` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/warehouse-operations/receive/`

**Принять груз**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/warehouse-operations/store/`

**Разместить в ячейку**

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `qr_code` | string | да |  |
| `cell` | string (uuid) | да |  |
| `reason` | string | нет |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `order` | string (uuid) | Заказ |
| `order_number` | string |  |
| `qr_code` | string | QR-код |
| `barcode` | string | Штрихкод |
| `title` | string | Наименование |
| `description` | string | Описание |
| `weight` | string (decimal) | Вес, кг |
| `length` | integer (int64) | Длина, см |
| `width` | integer (int64) | Ширина, см |
| `height` | integer (int64) | Высота, см |
| `volume` | string (decimal) | Объём, м³ |
| `declared_price` | string (decimal) | Объявленная ценность |
| `fragile` | boolean | Хрупкий |
| `dangerous` | boolean | Опасный |
| `status` | enum: `created` \| `received` \| `checked` \| `stored` \| `waiting_loading` \| `loaded` \| `in_transit` \| `unloaded` \| `ready_for_pickup` \| `delivered` \| `returned` \| `damaged` \| `lost` |  |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |


---

## warehouses

Склады, зоны и ячейки хранения

### `GET /api/v1/warehouse-cells/`

**Список: Ячейки склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `zone` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `zone` | string (uuid) | Зона |
| `zone_code` | string |  |
| `warehouse_code` | string |  |
| `code` | string | Код |
| `shelf` | string | Стеллаж |
| `row` | string | Ряд |
| `level` | string | Полка/уровень |
| `capacity_weight` | string (decimal) | Вместимость, кг |
| `capacity_volume` | string (decimal) | Вместимость, м³ |
| `occupied_weight` | string (decimal) | Занято, кг |
| `occupied_volume` | string (decimal) | Занято, м³ |
| `free_weight` | string (decimal) |  |
| `free_volume` | string (decimal) |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/warehouse-cells/`

**Создание: Ячейка склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `zone` | string (uuid) | да | Зона |
| `code` | string | да | Код |
| `shelf` | string | нет | Стеллаж |
| `row` | string | нет | Ряд |
| `level` | string | нет | Полка/уровень |
| `capacity_weight` | string (decimal) | да | Вместимость, кг |
| `capacity_volume` | string (decimal) | да | Вместимость, м³ |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `zone` | string (uuid) | Зона |
| `zone_code` | string |  |
| `warehouse_code` | string |  |
| `code` | string | Код |
| `shelf` | string | Стеллаж |
| `row` | string | Ряд |
| `level` | string | Полка/уровень |
| `capacity_weight` | string (decimal) | Вместимость, кг |
| `capacity_volume` | string (decimal) | Вместимость, м³ |
| `occupied_weight` | string (decimal) | Занято, кг |
| `occupied_volume` | string (decimal) | Занято, м³ |
| `free_weight` | string (decimal) |  |
| `free_volume` | string (decimal) |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/warehouse-cells/available/`

**Ячейки со свободной вместимостью**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `zone` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `zone` | string (uuid) | Зона |
| `zone_code` | string |  |
| `warehouse_code` | string |  |
| `code` | string | Код |
| `shelf` | string | Стеллаж |
| `row` | string | Ряд |
| `level` | string | Полка/уровень |
| `capacity_weight` | string (decimal) | Вместимость, кг |
| `capacity_volume` | string (decimal) | Вместимость, м³ |
| `occupied_weight` | string (decimal) | Занято, кг |
| `occupied_volume` | string (decimal) | Занято, м³ |
| `free_weight` | string (decimal) |  |
| `free_volume` | string (decimal) |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/warehouse-cells/{id}/`

**Детально: Ячейка склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `zone` | string (uuid) | Зона |
| `zone_code` | string |  |
| `warehouse_code` | string |  |
| `code` | string | Код |
| `shelf` | string | Стеллаж |
| `row` | string | Ряд |
| `level` | string | Полка/уровень |
| `capacity_weight` | string (decimal) | Вместимость, кг |
| `capacity_volume` | string (decimal) | Вместимость, м³ |
| `occupied_weight` | string (decimal) | Занято, кг |
| `occupied_volume` | string (decimal) | Занято, м³ |
| `free_weight` | string (decimal) |  |
| `free_volume` | string (decimal) |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/warehouse-cells/{id}/`

**Изменение: Ячейка склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `zone` | string (uuid) | нет | Зона |
| `code` | string | нет | Код |
| `shelf` | string | нет | Стеллаж |
| `row` | string | нет | Ряд |
| `level` | string | нет | Полка/уровень |
| `capacity_weight` | string (decimal) | нет | Вместимость, кг |
| `capacity_volume` | string (decimal) | нет | Вместимость, м³ |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `zone` | string (uuid) | Зона |
| `zone_code` | string |  |
| `warehouse_code` | string |  |
| `code` | string | Код |
| `shelf` | string | Стеллаж |
| `row` | string | Ряд |
| `level` | string | Полка/уровень |
| `capacity_weight` | string (decimal) | Вместимость, кг |
| `capacity_volume` | string (decimal) | Вместимость, м³ |
| `occupied_weight` | string (decimal) | Занято, кг |
| `occupied_volume` | string (decimal) | Занято, м³ |
| `free_weight` | string (decimal) |  |
| `free_volume` | string (decimal) |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/warehouse-cells/{id}/`

**Удаление (soft delete): Ячейка склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/warehouse-zones/`

**Список: Зоны склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |
| `type` | enum: `archive` \| `damaged` \| `dispatch` \| `receiving` \| `return` \| `storage` | * `receiving` - Приёмка
* `storage` - Хранение
* `dispatch` - Отгрузка
* `return` - Возвраты
* `damaged` - Повреждённые
* `archive` - Архив |
| `warehouse` | string (uuid) |  |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `warehouse_code` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `type` | enum: `receiving` \| `storage` \| `dispatch` \| `return` \| `damaged` \| `archive` |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/warehouse-zones/`

**Создание: Зона склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `warehouse` | string (uuid) | да | Склад |
| `name` | string | да | Название |
| `code` | string | да | Код |
| `type` | enum: `receiving` \| `storage` \| `dispatch` \| `return` \| `damaged` \| `archive` | нет | * `receiving` - Приёмка
* `storage` - Хранение
* `dispatch` - Отгрузка
* `return` - Возвраты
* `damaged` - Повреждённые
* `archive` - Архив |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `warehouse_code` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `type` | enum: `receiving` \| `storage` \| `dispatch` \| `return` \| `damaged` \| `archive` |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/warehouse-zones/{id}/`

**Детально: Зона склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `warehouse_code` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `type` | enum: `receiving` \| `storage` \| `dispatch` \| `return` \| `damaged` \| `archive` |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/warehouse-zones/{id}/`

**Изменение: Зона склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `warehouse` | string (uuid) | нет | Склад |
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `type` | enum: `receiving` \| `storage` \| `dispatch` \| `return` \| `damaged` \| `archive` | нет | * `receiving` - Приёмка
* `storage` - Хранение
* `dispatch` - Отгрузка
* `return` - Возвраты
* `damaged` - Повреждённые
* `archive` - Архив |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `warehouse` | string (uuid) | Склад |
| `warehouse_code` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `type` | enum: `receiving` \| `storage` \| `dispatch` \| `return` \| `damaged` \| `archive` |  |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/warehouse-zones/{id}/`

**Удаление (soft delete): Зона склада**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

### `GET /api/v1/warehouses/`

**Список: Склады**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Query-параметры:

| Параметр | Тип | Описание |
|---|---|---|
| `branch` | string (uuid) |  |
| `is_active` | boolean |  |
| `ordering` | string | Which field to use when ordering the results. |
| `page` | integer | A page number within the paginated result set. |
| `page_size` | integer | Number of results to return per page. |
| `search` | string | A search term. |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `manager` | string (uuid) | Заведующий |
| `manager_name` | string |  |
| `phone` | string | Телефон |
| `total_area` | string (decimal) | Площадь, м² |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `POST /api/v1/warehouses/`

**Создание: Склад**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `branch` | string (uuid) | да | Филиал |
| `name` | string | да | Название |
| `code` | string | да | Код |
| `address` | string | нет | Адрес |
| `manager` | string (uuid) | нет | Заведующий |
| `phone` | string | нет | Телефон |
| `total_area` | string (decimal) | нет | Площадь, м² |
| `max_weight` | string (decimal) | нет | Макс. вес, кг |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `manager` | string (uuid) | Заведующий |
| `manager_name` | string |  |
| `phone` | string | Телефон |
| `total_area` | string (decimal) | Площадь, м² |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `GET /api/v1/warehouses/{id}/`

**Детально: Склад**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `manager` | string (uuid) | Заведующий |
| `manager_name` | string |  |
| `phone` | string | Телефон |
| `total_area` | string (decimal) | Площадь, м² |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `PATCH /api/v1/warehouses/{id}/`

**Изменение: Склад**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

Тело запроса (JSON):

| Поле | Тип | Обяз. | Описание |
|---|---|---|---|
| `branch` | string (uuid) | нет | Филиал |
| `name` | string | нет | Название |
| `code` | string | нет | Код |
| `address` | string | нет | Адрес |
| `manager` | string (uuid) | нет | Заведующий |
| `phone` | string | нет | Телефон |
| `total_area` | string (decimal) | нет | Площадь, м² |
| `max_weight` | string (decimal) | нет | Макс. вес, кг |
| `is_active` | boolean | нет | Активен |

Ответ (`data`):

| Поле | Тип | Описание |
|---|---|---|
| `id` | string (uuid) |  |
| `branch` | string (uuid) | Филиал |
| `branch_name` | string |  |
| `name` | string | Название |
| `code` | string | Код |
| `address` | string | Адрес |
| `manager` | string (uuid) | Заведующий |
| `manager_name` | string |  |
| `phone` | string | Телефон |
| `total_area` | string (decimal) | Площадь, м² |
| `max_weight` | string (decimal) | Макс. вес, кг |
| `is_active` | boolean | Активен |
| `created_at` | string (date-time) | Создано |
| `updated_at` | string (date-time) | Обновлено |

### `DELETE /api/v1/warehouses/{id}/`

**Удаление (soft delete): Склад**

Права на уровне action во ViewSet.

permission_classes_by_action = {
    'create': [IsOperator],
    '__default__': [IsAuthenticated],
}

