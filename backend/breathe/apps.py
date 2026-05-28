from django.apps import AppConfig


class BreatheConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'breathe'
    
    def ready(self):
        """Import signals when app is ready."""
        from breathe.signals import enable_sqlite_foreign_keys  # noqa
