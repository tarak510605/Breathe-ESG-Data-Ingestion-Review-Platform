"""
Signal handlers for app initialization.
Enables SQLite foreign key constraints on startup.
"""
from django.db.backends.signals import connection_created
from django.dispatch import receiver
from django.conf import settings


@receiver(connection_created)
def enable_sqlite_foreign_keys(sender, connection, **kwargs):
    """Enable foreign key constraints for SQLite."""
    if 'sqlite' in connection.settings_dict['ENGINE']:
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys = ON;')
