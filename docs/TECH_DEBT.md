# Технический долг

Ведётся по Technical Debt Policy (ТЗ, раздел 21): каждый пункт имеет приоритет,
план устранения и срок (итерацию).

| # | Долг | Приоритет | План устранения | Срок |
|---|---|---|---|---|
| 1 | 2FA (SMS/Email/TOTP) для Finance/Director/SuperAdmin не реализована | Высокий | Вместе с модулем notifications и SMS Provider Interface | Этап 8 |
| 2 | Уведомление о входе с нового устройства (SMS/Email/Push) | Средний | Подписчик на событие user.logged_in после появления каналов | Этап 8 |
| 3 | mypy не включён в обязательный прогон (только black/isort/flake8) | Средний | Ввести mypy с django-stubs, поэтапно по модулям | Этап 2 |
| 5 | Гео-поля DeviceSession (country/city) не заполняются | Низкий | GeoIP-провайдер в integrations | Этап 8 |
| 7 | Rate-limit заголовки X-RateLimit-* не отдаются | Низкий | Middleware поверх DRF throttling | Этап 9 |
| 8 | JSON-логгер собран f-строкой формата, а не полноценным JSONFormatter | Низкий | python-json-logger или structlog | Этап 9 |

## Актуально после Этапов 1–9 (2026-07-05)

| # | Долг | Приоритет | План |
|---|---|---|---|
| 9 | WebSocket (Channels) для live-GPS/дашбордов — сейчас polling | Средний | Channels + Redis channel layer, деградация до polling сохраняется |
| 10 | Sentry/Prometheus/Grafana не подключены | Средний | django-prometheus + sentry-sdk, docker-сервисы мониторинга |
| 11 | Backup-скрипты (pg_dump ежедневно, AES-256, хранение 30 дней) | Высокий | cron-контейнер или systemd-timer на прод-сервере |
| 12 | MinIO/S3 для media (сейчас локальный volume) | Средний | django-storages + minio-сервис в prod-compose |
| 13 | Партиционирование GPSLog/AuditLog по месяцам | Средний | pg_partman при росте прод-данных |
| 14 | PDF-генерация счетов/накладных, Excel-экспорт | Средний | weasyprint/openpyxl отдельной итерацией |
| 15 | SystemSettings в БД (раздел 18) — пороги пока в константах сервисов | Средний | Модель настроек + кэш, миграция констант |
