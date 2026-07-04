"""Настройки для запуска тестов: быстрые, без внешних зависимостей (Postgres/Redis)."""

import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key-not-for-production')

from core.settings.base import *  # noqa: E402,F403

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Не сканировать несуществующий STATIC_ROOT при старте
WHITENOISE_AUTOREFRESH = True

REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    'DEFAULT_THROTTLE_CLASSES': (),
    'DEFAULT_THROTTLE_RATES': {
        'anon': '10000/min',
        'user': '10000/min',
        'driver': '10000/min',
        'auth': '10000/min',
    },
}

STORAGES = {
    **STORAGES,  # noqa: F405
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
