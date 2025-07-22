"""
Middleware avanzado para rate limiting y protección contra abusos.
"""
import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from blog.ratelimit import get_client_ip, ratelimit_view, is_suspicious_request

logger = logging.getLogger('django.security')


class AdvancedRateLimitMiddleware(MiddlewareMixin):
    """
    Middleware avanzado que implementa múltiples estrategias de rate limiting.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuración desde settings
        self.global_rate_limit = getattr(settings, 'GLOBAL_RATE_LIMIT', '1000/h')
        self.api_rate_limit = getattr(settings, 'API_RATE_LIMIT', '200/h')
        self.suspicious_rate_limit = getattr(settings, 'SUSPICIOUS_RATE_LIMIT', '10/m')
        
        # Rutas que requieren rate limiting especial
        self.api_paths = getattr(settings, 'API_PATHS', ['/api/', '/ajax/'])
        self.auth_paths = getattr(settings, 'AUTH_PATHS', ['/login/', '/register/', '/password/'])
        self.upload_paths = getattr(settings, 'UPLOAD_PATHS', ['/upload/', '/media/'])
        
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Procesa la solicitud antes de que llegue a la vista.
        """
        # Obtener información del cliente
        client_ip = get_client_ip(request)
        user_id = request.user.id if request.user.is_authenticated else None
        
        # Verificar si la solicitud es sospechosa
        is_suspicious, suspicious_factors = is_suspicious_request(request)
        
        # Aplicar rate limiting según el tipo de ruta
        if self._is_api_request(request):
            if not self._check_api_rate_limit(request, client_ip, user_id):
                return self._rate_limit_response(request)
        
        elif self._is_auth_request(request):
            if not self._check_auth_rate_limit(request, client_ip):
                return self._rate_limit_response(request)
        
        elif self._is_upload_request(request):
            if not self._check_upload_rate_limit(request, client_ip, user_id):
                return self._rate_limit_response(request)
        
        # Rate limiting para solicitudes sospechosas
        if is_suspicious:
            if not self._check_suspicious_rate_limit(request, client_ip):
                logger.warning(
                    f"Solicitud sospechosa bloqueada por rate limiting",
                    extra={
                        'ip': client_ip,
                        'path': request.path,
                        'factors': suspicious_factors,
                    }
                )
                return self._rate_limit_response(request)
        
        # Rate limiting global
        if not self._check_global_rate_limit(request, client_ip, user_id):
            return self._rate_limit_response(request)
        
        return None
    
    def _is_api_request(self, request):
        """Verifica si es una solicitud a la API."""
        return any(request.path.startswith(path) for path in self.api_paths)
    
    def _is_auth_request(self, request):
        """Verifica si es una solicitud de autenticación."""
        return any(request.path.startswith(path) for path in self.auth_paths)
    
    def _is_upload_request(self, request):
        """Verifica si es una solicitud de subida de archivos."""
        return (any(request.path.startswith(path) for path in self.upload_paths) or 
                request.FILES or 
                request.content_type.startswith('multipart/'))
    
    def _check_rate_limit(self, cache_key, rate, request_path=None):
        """
        Verifica un rate limit específico usando sliding window.
        
        Args:
            cache_key: Clave para el caché
            rate: Tasa en formato "número/período"
            request_path: Ruta de la solicitud (para logging)
        
        Returns:
            bool: True si está dentro del límite, False si se excede
        """
        try:
            count, period = rate.split('/')
            count = int(count)
        except ValueError:
            logger.error(f"Formato de tasa inválido: {rate}")
            return True
        
        # Mapeo de períodos a segundos
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        duration = duration_map.get(period, 3600)
        
        # Implementar sliding window
        now = time.time()
        window_start = now - duration
        
        # Obtener historial de solicitudes
        request_times = cache.get(cache_key, [])
        
        # Filtrar solicitudes dentro de la ventana
        request_times = [t for t in request_times if t > window_start]
        
        # Verificar límite
        if len(request_times) >= count:
            return False
        
        # Agregar solicitud actual
        request_times.append(now)
        
        # Guardar en caché
        cache.set(cache_key, request_times, duration + 60)
        
        return True
    
    def _check_global_rate_limit(self, request, client_ip, user_id):
        """Verifica el rate limit global."""
        identifier = str(user_id) if user_id else client_ip
        cache_key = f"global_rate_limit:{identifier}"
        return self._check_rate_limit(cache_key, self.global_rate_limit, request.path)
    
    def _check_api_rate_limit(self, request, client_ip, user_id):
        """Verifica el rate limit para APIs."""
        identifier = str(user_id) if user_id else client_ip
        cache_key = f"api_rate_limit:{identifier}"
        return self._check_rate_limit(cache_key, self.api_rate_limit, request.path)
    
    def _check_auth_rate_limit(self, request, client_ip):
        """Verifica el rate limit para autenticación (siempre por IP)."""
        cache_key = f"auth_rate_limit:{client_ip}"
        return self._check_rate_limit(cache_key, '10/m', request.path)
    
    def _check_upload_rate_limit(self, request, client_ip, user_id):
        """Verifica el rate limit para subidas."""
        identifier = str(user_id) if user_id else client_ip
        cache_key = f"upload_rate_limit:{identifier}"
        return self._check_rate_limit(cache_key, '20/m', request.path)
    
    def _check_suspicious_rate_limit(self, request, client_ip):
        """Verifica el rate limit para solicitudes sospechosas."""
        cache_key = f"suspicious_rate_limit:{client_ip}"
        return self._check_rate_limit(cache_key, self.suspicious_rate_limit, request.path)
    
    def _rate_limit_response(self, request):
        """Genera la respuesta de rate limit excedido."""
        client_ip = get_client_ip(request)
        
        logger.warning(
            f"Rate limit excedido en middleware",
            extra={
                'ip': client_ip,
                'user_id': getattr(request.user, 'id', None),
                'path': request.path,
                'method': request.method,
            }
        )
        
        return ratelimit_view(request)


class DDoSProtectionMiddleware(MiddlewareMixin):
    """
    Middleware para protección básica contra ataques DDoS.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuración
        self.ddos_threshold = getattr(settings, 'DDOS_THRESHOLD', '100/m')
        self.ddos_block_duration = getattr(settings, 'DDOS_BLOCK_DURATION', 3600)  # 1 hora
        
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Verifica patrones de DDoS y bloquea IPs sospechosas.
        """
        client_ip = get_client_ip(request)
        
        # Verificar si la IP está bloqueada
        block_key = f"ddos_blocked:{client_ip}"
        if cache.get(block_key):
            logger.warning(
                f"Solicitud bloqueada por protección DDoS",
                extra={'ip': client_ip, 'path': request.path}
            )
            return JsonResponse({
                'error': 'IP bloqueada temporalmente',
                'message': 'Su IP ha sido bloqueada debido a actividad sospechosa'
            }, status=429)
        
        # Verificar umbral de DDoS
        ddos_key = f"ddos_counter:{client_ip}"
        if not self._check_rate_limit(ddos_key, self.ddos_threshold):
            # Bloquear IP
            cache.set(block_key, True, self.ddos_block_duration)
            
            logger.critical(
                f"IP bloqueada por posible ataque DDoS",
                extra={
                    'ip': client_ip,
                    'path': request.path,
                    'threshold': self.ddos_threshold,
                    'block_duration': self.ddos_block_duration,
                }
            )
            
            return JsonResponse({
                'error': 'IP bloqueada por actividad sospechosa',
                'message': 'Su IP ha sido bloqueada debido a un patrón de tráfico anómalo'
            }, status=429)
        
        return None
    
    def _check_rate_limit(self, cache_key, rate):
        """Implementación simplificada de rate limiting para DDoS."""
        try:
            count, period = rate.split('/')
            count = int(count)
        except ValueError:
            return True
        
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        duration = duration_map.get(period, 60)
        
        current_count = cache.get(cache_key, 0)
        
        if current_count >= count:
            return False
        
        # Incrementar contador
        cache.set(cache_key, current_count + 1, duration)
        return True


class BotDetectionMiddleware(MiddlewareMixin):
    """
    Middleware para detectar y manejar bots maliciosos.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Patrones de User-Agent sospechosos
        self.suspicious_user_agents = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'python-urllib', 'scrapy'
        ]
        
        # User-Agents permitidos (bots legítimos)
        self.allowed_bots = [
            'googlebot', 'bingbot', 'slurp', 'duckduckbot',
            'baiduspider', 'yandexbot', 'facebookexternalhit'
        ]
        
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Detecta bots y aplica rate limiting específico.
        """
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        client_ip = get_client_ip(request)
        
        # Verificar si es un bot permitido
        if any(bot in user_agent for bot in self.allowed_bots):
            # Aplicar rate limiting suave para bots legítimos
            cache_key = f"bot_rate_limit:{client_ip}"
            if not self._check_bot_rate_limit(cache_key, '60/m'):
                logger.info(
                    f"Bot legítimo limitado por tasa",
                    extra={'ip': client_ip, 'user_agent': user_agent}
                )
                return ratelimit_view(request)
            return None
        
        # Verificar si es un bot sospechoso
        if any(pattern in user_agent for pattern in self.suspicious_user_agents):
            logger.warning(
                f"Bot sospechoso detectado",
                extra={'ip': client_ip, 'user_agent': user_agent, 'path': request.path}
            )
            
            # Aplicar rate limiting estricto
            cache_key = f"suspicious_bot:{client_ip}"
            if not self._check_bot_rate_limit(cache_key, '10/m'):
                return JsonResponse({
                    'error': 'Acceso denegado',
                    'message': 'Actividad automatizada detectada'
                }, status=429)
        
        return None
    
    def _check_bot_rate_limit(self, cache_key, rate):
        """Rate limiting específico para bots."""
        try:
            count, period = rate.split('/')
            count = int(count)
        except ValueError:
            return True
        
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        duration = duration_map.get(period, 60)
        
        current_count = cache.get(cache_key, 0)
        
        if current_count >= count:
            return False
        
        cache.set(cache_key, current_count + 1, duration)
        return True