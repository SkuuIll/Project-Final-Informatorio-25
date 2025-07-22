"""
Configuración avanzada de rate limiting para la API.
Proporciona decoradores y utilidades para proteger los endpoints de la API
contra abusos y ataques de fuerza bruta.
"""

import time
import logging
import hashlib
from functools import wraps
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.response import Response
from rest_framework import status

# No dependemos de ipware, usamos nuestra propia implementación
IPWARE_AVAILABLE = False

logger = logging.getLogger('django.security')

# Configuración de límites de tasa por tipo de endpoint
RATE_LIMITS = {
    'default': {
        'authenticated': '100/minute',
        'anonymous': '30/minute',
    },
    'search': {
        'authenticated': '60/minute',
        'anonymous': '20/minute',
    },
    'auth': {
        'authenticated': '20/minute',
        'anonymous': '10/minute',
    },
    'sensitive': {
        'authenticated': '30/minute',
        'anonymous': '5/minute',
    },
    'write': {
        'authenticated': '50/minute',
        'anonymous': '0/minute',  # No permitir escrituras anónimas
    },
}

def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente, considerando proxies.
    Utiliza ipware para una detección más robusta si está disponible.
    """
    if IPWARE_AVAILABLE:
        client_ip, is_routable = ipware_get_client_ip(request)
        if client_ip is not None:
            return client_ip
    
    # Implementación estándar como fallback
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
    Utiliza una combinación de IP y User-Agent para usuarios anónimos,
    y el ID de usuario para usuarios autenticados.
    """
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        # Para usuarios anónimos, usar IP + User-Agent (hash)
        ip = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:200]
        identifier = hashlib.md5(f"{ip}:{user_agent}".encode()).hexdigest()
    else:
        # Para usuarios autenticados, usar ID de usuario
        identifier = f"user:{request.user.id}"
    
    # Crear clave para el caché
    key = f"ratelimit:{group}:{identifier}"
    return key

def parse_rate(rate):
    """
    Parsea una cadena de tasa en formato "número/unidad" a un número y duración en segundos.
    
    Args:
        rate: Cadena en formato "número/unidad" donde unidad puede ser second, minute, hour, day
              o sus abreviaturas s, m, h, d.
    
    Returns:
        Tupla (count, duration) donde count es el número de solicitudes y duration es el período en segundos.
    """
    if '/' not in rate:
        raise ValueError(f"Formato de tasa inválido: {rate}")
    
    count, period = rate.split('/')
    count = int(count)
    
    # Normalizar el período
    period = period.strip().lower()
    
    # Mapeo de unidades a segundos
    time_units = {
        's': 1,
        'second': 1,
        'seconds': 1,
        'm': 60,
        'minute': 60,
        'minutes': 60,
        'h': 3600,
        'hour': 3600,
        'hours': 3600,
        'd': 86400,
        'day': 86400,
        'days': 86400,
    }
    
    if period not in time_units:
        raise ValueError(f"Unidad de tiempo no válida: {period}")
    
    duration = time_units[period]
    
    return count, duration

def api_rate_limit(group='default', rate=None):
    """
    Decorador avanzado para limitar la tasa de solicitudes a endpoints de API.
    
    Args:
        group: Grupo de rate limiting (para separar límites por tipo de operación)
        rate: Tasa en formato "número/unidad" donde unidad puede ser s, m, h, d
              Si no se especifica, se usa la configuración predeterminada según el grupo.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Omitir rate limiting para superusuarios y staff
            if hasattr(request, 'user') and request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff):
                return view_func(request, *args, **kwargs)
            
            # Determinar la tasa según el usuario esté autenticado o no
            if rate is None:
                # Usar configuración predeterminada según el grupo
                group_config = RATE_LIMITS.get(group, RATE_LIMITS['default'])
                if hasattr(request, 'user') and request.user.is_authenticated:
                    rate_str = group_config['authenticated']
                else:
                    rate_str = group_config['anonymous']
            else:
                rate_str = rate
            
            # Parsear la tasa
            try:
                count, duration = parse_rate(rate_str)
            except ValueError as e:
                logger.error(f"Error en configuración de rate limit: {e}")
                # Usar valores predeterminados seguros
                count, duration = 30, 60  # 30 por minuto
            
            # Generar clave de caché
            cache_key = get_cache_key(group, request)
            
            # Obtener contador actual
            now = time.time()
            window_start = int(now - duration)
            
            # Estructura en caché: {timestamp1: count1, timestamp2: count2, ...}
            request_history = cache.get(cache_key, {})
            
            # Limpiar entradas antiguas
            request_history = {ts: count for ts, count in request_history.items() if int(ts) > window_start}
            
            # Contar solicitudes en la ventana actual
            current_count = sum(request_history.values())
            
            # Verificar si se excede el límite
            if current_count >= count:
                # Registrar el intento de abuso
                ip = get_client_ip(request)
                user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
                
                logger.warning(
                    f"Rate limit excedido para {group}: {current_count}/{count} solicitudes",
                    extra={
                        'ip': ip,
                        'user_id': user_id,
                        'group': group,
                        'path': request.path,
                        'method': request.method,
                    }
                )
                
                # Responder según el tipo de solicitud
                if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
                    return JsonResponse({
                        'error': 'Rate limit exceeded',
                        'message': 'Has realizado demasiadas solicitudes. Por favor, intenta de nuevo más tarde.',
                        'retry_after': duration,
                    }, status=429)
                
                # Para solicitudes normales, usar la vista de rate limit
                from blog.ratelimit import ratelimit_view
                return ratelimit_view(request)
            
            # Actualizar contador
            current_timestamp = str(int(now))
            if current_timestamp in request_history:
                request_history[current_timestamp] += 1
            else:
                request_history[current_timestamp] = 1
            
            # Guardar en caché
            cache.set(cache_key, request_history, duration * 2)  # Doble duración para mantener historial
            
            # Ejecutar vista
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    
    return decorator

# Throttling classes para DRF
class CustomUserRateThrottle(UserRateThrottle):
    """
    Throttling personalizado para usuarios autenticados en DRF.
    """
    scope = 'user'
    
    def get_cache_key(self, request, view):
        """
        Usar una clave de caché más robusta que incluye el grupo.
        """
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
            
        return f"throttle:{self.scope}:{view.__class__.__name__}:{ident}"

class CustomAnonRateThrottle(AnonRateThrottle):
    """
    Throttling personalizado para usuarios anónimos en DRF.
    """
    scope = 'anon'
    
    def get_cache_key(self, request, view):
        """
        Usar una clave de caché más robusta que incluye el grupo y User-Agent.
        """
        ident = self.get_ident(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:50]
        user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
        
        return f"throttle:{self.scope}:{view.__class__.__name__}:{ident}:{user_agent_hash}"

# Decoradores específicos para diferentes tipos de endpoints
def search_rate_limit(rate=None):
    """
    Decorador específico para limitar búsquedas.
    """
    return api_rate_limit(group='search', rate=rate)

def auth_rate_limit(rate=None):
    """
    Decorador específico para limitar operaciones de autenticación.
    """
    return api_rate_limit(group='auth', rate=rate)

def sensitive_rate_limit(rate=None):
    """
    Decorador específico para limitar operaciones sensibles.
    """
    return api_rate_limit(group='sensitive', rate=rate)

def write_rate_limit(rate=None):
    """
    Decorador específico para limitar operaciones de escritura.
    """
    return api_rate_limit(group='write', rate=rate)