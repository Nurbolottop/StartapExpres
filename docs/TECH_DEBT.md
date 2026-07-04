# Технический долг

Ведётся по Technical Debt Policy (ТЗ, раздел 21): каждый пункт имеет приоритет,
план устранения и срок (итерацию).

| # | Долг | Приоритет | План устранения | Срок |
|---|---|---|---|---|
| 1 | 2FA (SMS/Email/TOTP) для Finance/Director/SuperAdmin не реализована | Высокий | Вместе с модулем notifications и SMS Provider Interface | Этап 8 |
| 2 | Уведомление о входе с нового устройства (SMS/Email/Push) | Средний | Подписчик на событие user.logged_in после появления каналов | Этап 8 |
| 3 | mypy не включён в обязательный прогон (только black/isort/flake8) | Средний | Ввести mypy с django-stubs, поэтапно по модулям | Этап 2 |
| 4 | Idempotency-Key механизм не реализован (критических POST ещё нет) | Высокий | Реализовать в common при создании orders/payments | Этап 2 |
| 5 | Гео-поля DeviceSession (country/city) не заполняются | Низкий | GeoIP-провайдер в integrations | Этап 8 |
| 6 | CI/CD pipeline отсутствует (линтеры/тесты локально) | Высокий | GitHub Actions: lint → tests → coverage → build | Этап 9 |
| 7 | Rate-limit заголовки X-RateLimit-* не отдаются | Низкий | Middleware поверх DRF throttling | Этап 9 |
| 8 | JSON-логгер собран f-строкой формата, а не полноценным JSONFormatter | Низкий | python-json-logger или structlog | Этап 9 |
