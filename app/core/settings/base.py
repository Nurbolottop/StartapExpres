import os
from datetime import timedelta
from pathlib import Path

from celery.schedules import crontab
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# PATHS
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise Exception('SECRET_KEY не задан в переменных окружения')


def _env_list(name: str) -> list[str]:
    raw = os.getenv(name, '').strip()
    return [item.strip() for item in raw.split(',') if item.strip()]


ALLOWED_HOSTS = _env_list('ALLOWED_HOSTS')
CSRF_TRUSTED_ORIGINS = _env_list('CSRF_TRUSTED_ORIGINS')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# =============================================================================
# APPLICATIONS
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    # Local apps
    'apps.common',
    'apps.users',
    'apps.branches',
    'apps.audit',
    'apps.vehicles',
    'apps.warehouses',
    'apps.tariffs',
    'apps.orders',
    'apps.packages',
    'apps.tracking',
    'apps.routes',
    'apps.shipments',
    'apps.gps',
    'apps.finance',
    'apps.analytics',
    'apps.notifications',
    'apps.integrations',
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'apps.common.middleware.RequestContextMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# =============================================================================
# URLS & WSGI
# =============================================================================
ROOT_URLCONF = 'core.urls'
WSGI_APPLICATION = 'core.wsgi.application'

# =============================================================================
# TEMPLATES
# =============================================================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# =============================================================================
# DATABASE
# =============================================================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': int(os.getenv('POSTGRES_PORT', 5432)),
        'CONN_MAX_AGE': 60,
    }
}

# =============================================================================
# AUTHENTICATION
# =============================================================================
AUTH_USER_MODEL = 'users.User'

# Argon2 — основной хэшер, PBKDF2 — fallback (ТЗ, раздел 30)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Парольная политика (ТЗ, раздел 30): 12+ символов, сложность
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'apps.common.password_validators.PasswordComplexityValidator'},
]

# =============================================================================
# REST FRAMEWORK
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_RENDERER_CLASSES': ('apps.common.renderers.EnvelopeJSONRenderer',),
    'DEFAULT_PAGINATION_CLASS': 'apps.common.pagination.DefaultPageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'apps.common.throttling.RoleRateThrottle',
    ),
    # Rate limits (ТЗ, разделы 13, 30)
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '5000/day',
        'driver': '10000/day',
        'auth': '10/min',
        'gps': '12/min',
    },
    'DEFAULT_SCHEMA_CLASS': 'apps.common.schema.RussianAutoSchema',
    'EXCEPTION_HANDLER': 'apps.common.exceptions.exception_handler',
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

API_DESCRIPTION = """
ERP-система управления экспресс-доставкой грузов: заказы, склад, рейсы,
GPS-мониторинг, финансы, аналитика.

## Авторизация

1. `POST /api/v1/auth/login/` — вход по телефону и паролю, в ответе `access` и `refresh` токены.
2. Нажмите кнопку **Authorize** и вставьте access-токен (формат: `Bearer <токен>` подставится автоматически).
3. Access живёт 30 минут — обновляйте через `POST /api/v1/auth/refresh/`.

## Формат ответов

Все ответы — в едином конверте:

```json
{"success": true, "message": "Success", "data": {...}, "meta": {"page": 1, "total": 254}}
```

Ошибки:

```json
{"success": false, "message": "Ошибка валидации данных.",
 "error": {"code": "VALIDATION_ERROR", "fields": {...}}}
```

Коды ошибок — машиночитаемые: `AUTH_001..006`, `ORDER_001..010`, `SHIPMENT_001..009`,
`PACKAGE_001..007`, `PAYMENT_001..006`, `GPS_001..006`, `WAREHOUSE_001..006`.

## Роли

`client` — только свои заказы · `operator` — заказы, клиенты, рейсы ·
`warehouse` — складские операции и сканирование · `driver` — свои рейсы и GPS ·
`finance` — платежи, касса, возвраты · `director` — просмотр всего · `superadmin` — всё.

## Идемпотентность

Критические POST (создание заказа, оплата, возврат, создание рейса) поддерживают
заголовок `Idempotency-Key`: повторный запрос с тем же ключом не продублирует операцию.
"""

SPECTACULAR_SETTINGS = {
    'TITLE': 'Express Delivery ERP API',
    'DESCRIPTION': API_DESCRIPTION,
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
    'TAGS': [
        {'name': 'auth', 'description': 'Регистрация, вход, JWT-токены, профиль, сессии устройств'},
        {'name': 'users', 'description': 'Управление пользователями (SuperAdmin/Director)'},
        {'name': 'clients', 'description': 'Работа операторов с клиентами'},
        {'name': 'cities', 'description': 'Справочник городов'},
        {'name': 'branches', 'description': 'Филиалы компании'},
        {'name': 'warehouses', 'description': 'Склады, зоны и ячейки хранения'},
        {
            'name': 'warehouse-operations',
            'description': 'Складские процессы: приём, размещение, перемещение, инвентаризация, выдача',
        },
        {'name': 'vehicles', 'description': 'Автопарк и назначение водителей'},
        {'name': 'routes', 'description': 'Маршруты между филиалами'},
        {'name': 'tariffs', 'description': 'Тарифы, дополнительные услуги, калькулятор стоимости'},
        {'name': 'orders', 'description': 'Заказы: создание, подтверждение, оплата, статусы (FSM), история'},
        {'name': 'packages', 'description': 'Грузовые места: QR/штрихкоды, фотофиксация, сканирование'},
        {
            'name': 'shipments',
            'description': 'Рейсы: состав, погрузка/разгрузка по сканам, жизненный цикл, инциденты',
        },
        {
            'name': 'gps',
            'description': 'GPS-мониторинг: координаты водителей, онлайн-карта, история, геозоны',
        },
        {
            'name': 'finance',
            'description': 'Платежи, счета, касса, задолженности, возвраты, финансовые отчёты',
        },
        {'name': 'dashboard', 'description': 'Ролевой дашборд'},
        {'name': 'reports', 'description': 'Аналитические отчёты'},
        {'name': 'notifications', 'description': 'Уведомления и шаблоны'},
        {'name': 'audit', 'description': 'Журнал аудита (только чтение)'},
        {'name': 'health', 'description': 'Проверки живости сервиса и зависимостей'},
    ],
    'ENUM_NAME_OVERRIDES': {
        'OrderStatusEnum': 'apps.orders.choices.OrderStatus',
        'PackageStatusEnum': 'apps.packages.choices.PackageStatus',
        'VehicleStatusEnum': 'apps.vehicles.choices.VehicleStatus',
        'EmployeeStatusEnum': 'apps.users.choices.EmployeeStatus',
        'DriverStatusEnum': 'apps.users.choices.DriverStatus',
        'ZoneTypeEnum': 'apps.warehouses.choices.ZoneType',
        'PhotoTypeEnum': 'apps.packages.choices.PhotoType',
        'PaymentTypeEnum': 'apps.orders.choices.PaymentType',
        'DeliveryTypeEnum': 'apps.orders.choices.DeliveryType',
        'FuelTypeEnum': 'apps.vehicles.choices.FuelType',
    },
}

# =============================================================================
# CORS
# =============================================================================
CORS_ALLOWED_ORIGINS = _env_list('CORS_ALLOWED_ORIGINS')

# =============================================================================
# CACHE (REDIS)
# =============================================================================
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }
}

# =============================================================================
# CELERY
# =============================================================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300

# Фоновые проверки (ТЗ, разделы 10, 20)
CELERY_BEAT_SCHEDULE = {
    'gps-check-offline': {
        'task': 'gps.check_offline_vehicles',
        'schedule': 300.0,  # каждые 5 минут
        'options': {'queue': 'gps'},
    },
    'gps-detect-long-stops': {
        'task': 'gps.detect_long_stops',
        'schedule': 300.0,
        'options': {'queue': 'gps'},
    },
}
CELERY_BEAT_SCHEDULE.update(
    {
        'finance-daily-report': {
            'task': 'finance.build_daily_report',
            'schedule': crontab(hour=23, minute=59),  # ТЗ, раздел 11
            'options': {'queue': 'finance'},
        },
        'finance-monthly-report': {
            'task': 'finance.build_monthly_report',
            'schedule': crontab(day_of_month=1, hour=0, minute=30),
            'options': {'queue': 'finance'},
        },
        'finance-check-overdue-debts': {
            'task': 'finance.check_overdue_debts',
            'schedule': crontab(hour=9, minute=0),
            'options': {'queue': 'finance'},
        },
    }
)
CELERY_TASK_ROUTES = {
    'gps.*': {'queue': 'gps'},
    'finance.*': {'queue': 'finance'},
    'notifications.*': {'queue': 'notifications'},
}

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ru')
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Bishkek')
USE_I18N = True
USE_TZ = True

# Языки API: message и ошибки локализуются по Accept-Language (ru|ky|en)
LANGUAGES = [
    ('ru', 'Русский'),
    ('ky', 'Кыргызча'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

CELERY_TIMEZONE = TIME_ZONE

# =============================================================================
# INTEGRATIONS (Provider Interface — ТЗ, раздел 16)
# =============================================================================
# Путь к JSON сервисного аккаунта Firebase; пусто — push пишется в лог
FIREBASE_CREDENTIALS_FILE = os.getenv('FIREBASE_CREDENTIALS_FILE', '')

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# =============================================================================
# LOGGING
# =============================================================================
# Структурированные JSON-логи с request_id/correlation_id (ТЗ, раздел 29)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'request_context': {
            '()': 'apps.common.logging.RequestContextFilter',
        },
    },
    'formatters': {
        'json': {
            'format': (
                '{{"timestamp": "{asctime}", "level": "{levelname}", "logger": "{name}", '
                '"request_id": "{request_id}", "correlation_id": "{correlation_id}", '
                '"message": {message!r}}}'
            ),
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['request_context'],
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.getenv('LOG_LEVEL', 'INFO'),
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# =============================================================================
# DEFAULTS
# =============================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
