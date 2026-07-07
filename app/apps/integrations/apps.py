from django.apps import AppConfig


class IntegrationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.integrations'
    verbose_name = 'Интеграции'

    def ready(self) -> None:
        from apps.integrations.providers import configure_providers

        configure_providers()
