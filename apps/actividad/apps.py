from django.apps import AppConfig


class ActividadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.actividad'

    def ready(self):
        import apps.actividad.signals  # noqa: F401
