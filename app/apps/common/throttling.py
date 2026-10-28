"""Rate limit по ролям (ТЗ, раздел 30): Client 5000/день, Driver 10000/день."""

from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.choices import Roles


class RoleRateThrottle(UserRateThrottle):
    scope = 'user'
    driver_scope = 'driver'

    def allow_request(self, request, view) -> bool:
        user = getattr(request, 'user', None)
        if user and user.is_authenticated and getattr(user, 'role', None) == Roles.DRIVER:
            self.scope = self.driver_scope
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)
        return super().allow_request(request, view)


class RefreshTokenThrottle(SimpleRateThrottle):
    """Лимит /auth/refresh/ по пользователю из refresh-токена, а не по IP.

    Access живёт 30 минут — устройство обновляется ~48 раз в сутки, а склад и
    водители сидят за одним офисным NAT: анонимные 100/день на IP кончаются
    за пару устройств. Невалидный токен считаем по IP.
    """

    scope = 'refresh'

    def get_cache_key(self, request, view):
        try:
            token = RefreshToken(request.data.get('refresh', ''))
            ident = f'user:{token[jwt_settings.USER_ID_CLAIM]}'
        except (TokenError, KeyError, TypeError):
            ident = f'ip:{self.get_ident(request)}'
        return self.cache_format % {'scope': self.scope, 'ident': ident}
