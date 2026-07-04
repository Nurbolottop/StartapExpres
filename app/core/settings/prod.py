from core.settings.base import *  # noqa: F403

DEBUG = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# TLS терминируется на nginx перед приложением
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 2592000  # 30 дней
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# W008: редирект http→https выполняет nginx; W021: preload — осознанное решение,
# требует безотзывной регистрации домена в браузерных списках
SILENCED_SYSTEM_CHECKS = ['security.W008', 'security.W021']
