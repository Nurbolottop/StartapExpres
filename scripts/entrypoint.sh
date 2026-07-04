#!/bin/sh
set -e

echo "Ожидание доступности PostgreSQL (${POSTGRES_HOST}:${POSTGRES_PORT})..."
until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "Применяем миграции..."
python manage.py migrate --noinput

echo "Собираем статические файлы..."
python manage.py collectstatic --noinput

exec "$@"
