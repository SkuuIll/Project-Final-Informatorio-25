"""
DevBlog application.
"""

# Configurar Celery
from .celery import app as celery_app

__all__ = ['celery_app']

# Configure the default app config
default_app_config = 'blog.apps.BlogConfig'