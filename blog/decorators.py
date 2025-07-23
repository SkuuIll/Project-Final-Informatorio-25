"""
Decoradores personalizados para el proyecto.
"""
import json
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit


def ajax_login_required(view_func):
    """
    Decorador que requiere autenticación para vistas AJAX.
    Devuelve JSON en lugar de redirigir a la página de login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Debes iniciar sesión para realizar esta acción',
                'redirect': '/accounts/login/'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper


def require_ajax_post(view_func):
    """
    Decorador que requiere que la solicitud sea POST y AJAX.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.method != 'POST':
            return JsonResponse({
                'success': False,
                'error': 'Método no permitido'
            }, status=405)
        
        # Verificar si es una solicitud AJAX
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Esta acción requiere AJAX'
            }, status=400)
            
        return view_func(request, *args, **kwargs)
    return wrapper


def ajax_required(view_func):
    """
    Decorador que combina ajax_login_required y require_ajax_post.
    """
    @wraps(view_func)
    @ajax_login_required
    @require_ajax_post
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


def sensitive_post_limit(rate='5/minute', group=None):
    """
    Decorador para limitar acciones sensibles como cambios de perfil.
    """
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key='user', rate=rate, method='POST', block=True, group=group)
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def user_action_limit(rate='10/minute', group=None):
    """
    Decorador para limitar acciones generales del usuario.
    """
    def decorator(view_func):
        @wraps(view_func)
        @ratelimit(key='user', rate=rate, method='POST', block=True, group=group)
        def wrapper(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator