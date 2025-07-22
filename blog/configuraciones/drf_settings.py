"""
Configuración de Django Rest Framework con rate limiting avanzado.
"""

from blog.api_ratelimit import CustomUserRateThrottle, CustomAnonRateThrottle

# Configuración de Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'blog.api_ratelimit.CustomUserRateThrottle',
        'blog.api_ratelimit.CustomAnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/minute',
        'anon': '30/minute',
        'auth': '20/minute',
        'search': '60/minute',
        'sensitive': '30/minute',
        'write': '50/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'EXCEPTION_HANDLER': 'blog.api_exceptions.custom_exception_handler',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
}