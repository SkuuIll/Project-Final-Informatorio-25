"""
Blog application configuration.
"""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Blog'

    def ready(self):
        """
        Initialize the application when Django is ready.
        This is the proper place to connect signals.
        """
        # Import and connect cache signals
        from .cache_signals import connect_cache_signals
        connect_cache_signals()