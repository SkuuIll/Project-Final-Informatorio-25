"""
Sistema simplificado de rate limiting para compatibilidad.
"""

from functools import wraps
import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

logger = logging.getLogger('django.security')

def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente, considerando proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Tomar la primera IP (la del cliente original)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip

def get_cache_key(group, request):
    """
    Genera una clave de caché única para el rate limiting.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        # Para usuarios anónimos, usar IP
        identifier = get_client_ip(request)
    else:
        # Para usuarios autenticados, usar ID de usuario
        identifier = str(request.user.id)
    
    # Crear hash para la clave
    key = f"ratelimit:{group}:{identifier}"
    return key

def parse_rate(rate):
    """
    Parsea una cadena de tasa en formato "número/unidad".
    """
    if '/' not in rate:
        raise ValueError(f"Formato de tasa inválido: {rate}")
    
    count, period = rate.split('/')
    count = int(count)
    
    # Normalizar el período
    period = period.strip().lower()
    
    # Mapeo de unidades a segundos
    time_units = {
        's': 1, 'second': 1, 'seconds': 1,
        'm': 60, 'minute': 60, 'minutes': 60,
        'h': 3600, 'hour': 3600, 'hours': 3600,
        'd': 86400, 'day': 86400, 'days': 86400,
    }
    
    if period not in time_units:
        raise ValueError(f"Unidad de tiempo no válida: {period}")
    
    duration = time_units[period]
    return count, duration

def api_rate_limit(group='api', rate='100/minute'):
    """
    Decorador simplificado para limitar la tasa de solicitudes.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Omitir rate limiting para superusuarios
            if hasattr(request, 'user') and request.user.is_authenticated and request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            try:
                count, duration = parse_rate(rate)
            except ValueError as e:
                logger.error(f"Error en configuración de rate limit: {e}")
                # Usar valores predeterminados seguros
                count, duration = 30, 60  # 30 por minuto
            
            # Generar clave de caché
            cache_key = get_cache_key(group, request)
            
            # Obtener contador actual
            now = time.time()
            window_start = int(now - duration)
            
            # Estructura en caché: lista de timestamps
            request_times = cache.get(cache_key, [])
            
            # Filtrar solicitudes dentro de la ventana
            request_times = [t for t in request_times if t > window_start]
            
            # Verificar si se excede el límite
            if len(request_times) >= count:
                logger.warning(
                    f"Rate limit excedido para {group}: {len(request_times)}/{count} solicitudes",
                    extra={
                        'ip': get_client_ip(request),
                        'user_id': getattr(request.user, 'id', None),
                        'group': group,
                        'path': request.path,
                    }
                )
                
                # Responder según el tipo de solicitud
                if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': _('Has realizado demasiadas solicitudes. Por favor, intenta de nuevo más tarde.'),
                        'retry_after': 60,
                    }, status=429)
                
                # Para solicitudes normales, mostrar página de error
                return render(request, 'ratelimit.html', {
                    'retry_after': 60,
                }, status=429)
            
            # Agregar solicitud actual
            request_times.append(now)
            
            # Guardar en caché
            cache.set(cache_key, request_times, duration + 60)
            
            # Ejecutar vista
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    
    return decorator

def search_rate_limit(rate='30/minute'):
    """
    Decorador específico para limitar búsquedas.
    """
    return api_rate_limit(group='search', rate=rate)

def auth_rate_limit(rate='10/minute'):
    """
    Decorador específico para limitar operaciones de autenticación.
    """
    return api_rate_limit(group='auth', rate=rate)

def sensitive_rate_limit(rate='20/minute'):
    """
    Decorador específico para limitar operaciones sensibles.
    """
    return api_rate_limit(group='sensitive', rate=rate)

def write_rate_limit(rate='30/minute'):
    """
    Decorador específico para limitar operaciones de escritura.
    """
    return api_rate_limit(group='write', rate=rate)