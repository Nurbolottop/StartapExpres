"""Rate limit по ролям (ТЗ, раздел 30): Client 5000/день, Driver 10000/день."""

from rest_framework.throttling import UserRateThrottle

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
