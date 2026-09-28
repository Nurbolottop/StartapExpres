"""Argon2 с параметрами под слабый прод-сервер (1 CPU, 2 ГБ RAM).

Дефолт Django (100 МБ памяти, 8 потоков) при нехватке RAM уводит воркер
в своп — регистрация/вход занимали 10–25 с. Параметры — минимальная
рекомендация OWASP для Argon2id: 19 МБ, 2 прохода, 1 поток. Алгоритм тот же
('argon2'), параметры хранятся в самом хэше, поэтому старые пароли проверяются
как раньше и пересчитываются с новыми параметрами при следующем входе.
"""

from django.contrib.auth.hashers import Argon2PasswordHasher


class LightArgon2PasswordHasher(Argon2PasswordHasher):
    memory_cost = 19 * 1024  # KiB
    time_cost = 2
    parallelism = 1
