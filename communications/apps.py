from django.apps import AppConfig


class CommunicationsConfig(AppConfig):
    name = 'communications'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import communications.signals  # noqa: F401
