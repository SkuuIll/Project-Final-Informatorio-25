"""
Utilidades para rate limiting y protección contra abusos.
Implementa límites de tasa configurables para diferentes tipos de solicitudes.
"""

import logging
import time
import hashlib
from functools import wraps
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.core.cache import cache
from django.conf import settings
from django.utils.decorators import sync_and_async_middleware
from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from blog.ratelimit_config import get_rate_limit, RATELIMIT_TIMEOUTS, PROGRESSIVE_RATELIMIT


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

def ratelimit_view(request, exception=None, block_time=None):
    """
    Vista para mostrar cuando se excede el rate limit.
    
    Args:
        request: Objeto request de Django
        exception: Excepción que causó el rate limit (opcional)
        block_time: Tiempo de bloqueo en segundos (opcional)
    """
    ip = get_client_ip(request)
    
    # Usar tiempo de bloqueo predeterminado si no se especifica
    if block_time is None:
        block_time = RATELIMIT_TIMEOUTS.get('default', 60)
    
    # Registrar el intento de abuso
    logger.warning(
        f"Rate limit excedido: {request.method} {request.path} (bloqueo: {block_time}s)",
        extra={
            'ip': ip,
            'user_id': getattr(request.user, 'id', None),
            'path': request.path,
            'method': request.method,
            'block_time': block_time,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    )
    
    # Responder según el tipo de solicitud
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        return JsonResponse({
            'error': 'Rate limit exceeded',
            'message': _('Has realizado demasiadas solicitudes. Por favor, intenta de nuevo más tarde.'),
            'retry_after': block_time,  # Segundos hasta que puedan intentar de nuevo
        }, status=429, headers={'Retry-After': str(block_time)})
    
    # Para solicitudes normales, mostrar página de error
    return render(request, 'ratelimit.html', {
        'retry_after': block_time,
        'retry_minutes': round(block_time / 60, 1) if block_time > 60 else None,
    }, status=429)

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

@sync_and_async_middleware
def api_rate_limit(get_response=None, *, group='api_default', rate=None):
    """
    Decorador para limitar la tasa de solicitudes a endpoints de API.
    Compatible con vistas síncronas y asíncronas.
    
    Args:
        group: Grupo de rate limiting (para separar límites por tipo de operación)
        rate: Tasa en formato "número/unidad" donde unidad puede ser s, m, h, d
              Ejemplos: "100/m" (100 por minuto), "5/s" (5 por segundo)
              Si es None, se usa la configuración del grupo
    """
    if get_response is None:
        # Si se usa como decorador con argumentos
        def decorator(view_func):
            return api_rate_limit(view_func, group=group, rate=rate)
        return decorator

    def _check_rate_limit(request):
        """Función auxiliar para verificar el rate limit"""
        # Determinar la tasa según el usuario y grupo
        effective_rate = rate or get_rate_limit(group, getattr(request, 'user', None))
        
        # Parsear la tasa
        count, period = effective_rate.split('/')
        count = int(count)
        
        # Determinar duración en segundos
        if period == 's':
            duration = 1
        elif period == 'm':
            duration = 60
        elif period == 'h':
            duration = 3600
        elif period == 'd':
            duration = 86400
        else:
            raise ValueError(f"Unidad de tiempo no válida: {period}")
        
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
            # Verificar si es abuso repetido
            abuse_key = f"abuse:{group}:{get_client_ip(request)}"
            abuse_count = cache.get(abuse_key, 0)
            
            # Incrementar contador de abuso
            cache.set(abuse_key, abuse_count + 1, 86400)  # 24 horas
            
            # Determinar tiempo de bloqueo según nivel de abuso
            if PROGRESSIVE_RATELIMIT['enabled']:
                # Bloqueo progresivo
                block_time = min(
                    PROGRESSIVE_RATELIMIT['base_timeout'] * (PROGRESSIVE_RATELIMIT['multiplier'] ** abuse_count),
                    PROGRESSIVE_RATELIMIT['max_timeout']
                )
            else:
                # Bloqueo fijo según nivel de abuso
                if abuse_count > 5:
                    block_time = RATELIMIT_TIMEOUTS.get('severe_abuse', 3600)
                elif abuse_count > 2:
                    block_time = RATELIMIT_TIMEOUTS.get('repeated_abuse', 300)
                else:
                    block_time = RATELIMIT_TIMEOUTS.get('default', 60)
            
            logger.warning(
                f"Rate limit excedido para {group}: {current_count}/{count} solicitudes (abuso #{abuse_count+1})",
                extra={
                    'ip': get_client_ip(request),
                    'user_id': getattr(request.user, 'id', None),
                    'group': group,
                    'path': request.path,
                    'abuse_count': abuse_count + 1,
                    'block_time': block_time,
                }
            )
            return ratelimit_view(request, block_time=block_time)
        
        # Actualizar contador
        current_timestamp = str(int(now))
        if current_timestamp in request_history:
            request_history[current_timestamp] += 1
        else:
            request_history[current_timestamp] = 1
        
        # Guardar en caché
        cache.set(cache_key, request_history, duration * 2)  # Doble duración para mantener historial

    if iscoroutinefunction(get_response):
        async def middleware(request):
            response = _check_rate_limit(request)
            if response:
                return response
            return await get_response(request)
    else:
        def middleware(request):
            response = _check_rate_limit(request)
            if response:
                return response
            return get_response(request)

    markcoroutinefunction(middleware)
    return middleware


def search_rate_limit(group='search', rate=None):
    """
    Decorador específico para limitar búsquedas.
    """
    return api_rate_limit(group=group, rate=rate)

def user_action_limit(group='user_action', rate=None):
    """
    Decorador para limitar acciones de usuario (comentarios, likes, etc).
    """
    return api_rate_limit(group=group, rate=rate)

def login_rate_limit(group='login_attempts', rate=None):
    """
    Decorador específico para limitar intentos de inicio de sesión.
    """
    return api_rate_limit(group=group, rate=rate)

def register_rate_limit(group='register_attempts', rate=None):
    """
    Decorador específico para limitar intentos de registro.
    """
    return api_rate_limit(group=group, rate=rate)

def ai_generation_limit(group='ai_generation', rate=None):
    """
    Decorador específico para limitar generación de contenido con IA.
    """
    return api_rate_limit(group=group, rate=rate)

def progressive_rate_limit(request, group, base_rate=100, period=60):
    """
    Implementa un rate limit progresivo que se vuelve más restrictivo
    con el uso excesivo.
    
    Args:
        request: Objeto request de Django
        group: Grupo de rate limiting
        base_rate: Tasa base permitida
        period: Período en segundos
    
    Returns:
        (allowed, current_limit): Tupla con booleano indicando si está permitido
                                 y el límite actual
    """
    cache_key = f"prog_ratelimit:{group}:{get_client_ip(request)}"
    abuse_key = f"abuse:{group}:{get_client_ip(request)}"
    
    # Verificar si el usuario está en la lista de abuso
    abuse_count = cache.get(abuse_key, 0)
    
    # Calcular límite actual (se reduce con cada abuso)
    current_limit = max(5, base_rate // (2 ** abuse_count))
    
    # Obtener contador actual
    counter = cache.get(cache_key, 0)
    
    # Verificar límite
    if counter >= current_limit:
        # Incrementar contador de abuso
        cache.set(abuse_key, abuse_count + 1, 86400)  # 24 horas
        return False, current_limit
    
    # Incrementar contador
    cache.set(cache_key, counter + 1, period)
    
    return True, current_limit

def is_suspicious_request(request):
    """
    Detecta si una solicitud parece sospechosa basándose en varios factores.
    """
    suspicious_factors = []
    
    # Verificar User-Agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if not user_agent or len(user_agent) < 10:
        suspicious_factors.append('user_agent_missing')
    
    # Verificar Accept header
    accept = request.META.get('HTTP_ACCEPT', '')
    if not accept:
        suspicious_factors.append('accept_missing')
    
    # Verificar Referer para solicitudes no API
    if not request.path.startswith('/api/'):
        referer = request.META.get('HTTP_REFERER', '')
        if not referer:
            suspicious_factors.append('referer_missing')
    
    # Verificar patrones de solicitud sospechosos
    if request.method == 'POST' and not request.POST and not request.FILES:
        suspicious_factors.append('empty_post')
    
    # Verificar cabeceras inconsistentes
    if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' and 'text/html' in accept:
        suspicious_factors.append('inconsistent_ajax')
    
    # Verificar solicitudes rápidas (requiere sesión)
    if hasattr(request, 'session'):
        last_request = request.session.get('last_request_time', 0)
        now = time.time()
        if last_request > 0 and now - last_request < 0.5:  # Menos de 500ms entre solicitudes
            suspicious_factors.append('rapid_requests')
        request.session['last_request_time'] = now
    
    # Determinar nivel de sospecha
    suspicion_level = len(suspicious_factors)
    
    # Registrar solicitudes muy sospechosas
    if suspicion_level >= 3:
        logger.warning(
            f"Solicitud altamente sospechosa detectada",
            extra={
                'ip': get_client_ip(request),
                'user_id': getattr(request.user, 'id', None),
                'path': request.path,
                'method': request.method,
                'factors': suspicious_factors,
            }
        )
    
    return suspicion_level >= 2, suspicious_factors
