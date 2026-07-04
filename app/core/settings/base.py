import os
from datetime import timedelta
from pathlib import Path

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
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
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

SPECTACULAR_SETTINGS = {
    'TITLE': 'Express Delivery ERP API',
    'DESCRIPTION': 'ERP-система управления экспресс-доставкой грузов.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
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
CELERY_TASK_ROUTES = {
    'gps.*': {'queue': 'gps'},
}

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ru')
TIME_ZONE = os.getenv('TIME_ZONE', 'Asia/Bishkek')
USE_I18N = True
USE_TZ = True

CELERY_TIMEZONE = TIME_ZONE

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
