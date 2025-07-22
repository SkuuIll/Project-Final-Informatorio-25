"""
Decoradores para vistas y funciones de la aplicación.
"""
import functools
from django.utils.decorators import method_decorator
from .ratelimit import (
    api_rate_limit, 
    search_rate_limit, 
    user_action_limit,
    login_rate_limit,
    register_rate_limit,
    ai_generation_limit
)

# Re-exportar decoradores de ratelimit para compatibilidad
__all__ = [
    'api_rate_limit', 
    'search_rate_limit', 
    'user_action_limit',
    'login_rate_limit',
    'register_rate_limit',
    'ai_generation_limit',
    'api_view_rate_limit',
    'class_view_rate_limit',
    'sensitive_post_limit'
]

def sensitive_post_limit(group='sensitive_posts', rate=None):
    """
    Decorador específico para limitar operaciones sensibles en posts.
    """
    return api_rate_limit(group=group, rate=rate)

def api_view_rate_limit(group='api_default', rate=None):
    """
    Decorador para aplicar rate limiting a vistas de función de API.
    
    Args:
        group: Grupo de rate limiting
        rate: Tasa en formato "número/unidad" (opcional)
    """
    def decorator(view_func):
        @api_rate_limit(group=group, rate=rate)
        @functools.wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def class_view_rate_limit(group='api_default', rate=None):
    """
    Decorador para aplicar rate limiting a vistas de clase de API.
    
    Args:
        group: Grupo de rate limiting
        rate: Tasa en formato "número/unidad" (opcional)
    """
    def decorator(view_class):
        view_class.dispatch = method_decorator(
            api_rate_limit(group=group, rate=rate)
        )(view_class.dispatch)
        return view_class
    return decorator