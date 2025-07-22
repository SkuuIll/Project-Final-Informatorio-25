"""
Middleware para caché automático de páginas y respuestas.
"""

import time
import hashlib
from django.core.cache import cache
from django.utils.cache import get_cache_key
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from blog.cache_utils import make_cache_key, cache_page_data, get_cached_data


class SmartCacheMiddleware(MiddlewareMixin):
    """
    Middleware inteligente que cachea automáticamente páginas según su tipo.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Configuración de caché por tipo de página
        self.cache_config = {
            '/': 300,  # Homepage - 5 minutos
            '/posts/': 300,  # Lista de posts - 5 minutos
            '/post/': 600,  # Detalle de post - 10 minutos
            '/search/': 180,  # Búsquedas - 3 minutos
            '/tag/': 900,  # Páginas de tags - 15 minutos
            '/api/': 60,  # API - 1 minuto
        }
        
        # Rutas que NO deben cachearse
        self.no_cache_paths = [
            '/admin/',
            '/login/',
            '/logout/',
            '/dashboard/',
            '/accounts/',
        ]
        
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Verifica si existe una versión cacheada de la página.
        """
        # No cachear para usuarios autenticados en ciertas páginas
        # Verificar si el usuario está disponible (después del middleware de autenticación)
        if (hasattr(request, 'user') and 
            request.user and
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated and 
            any(request.path.startswith(path) for path in ['/dashboard/', '/admin/'])):
            return None
        
        # No cachear rutas específicas
        if any(request.path.startswith(path) for path in self.no_cache_paths):
            return None
        
        # No cachear solicitudes POST
        if request.method != 'GET':
            return None
        
        # Generar clave de caché
        cache_key = self._get_cache_key(request)
        
        # Intentar obtener respuesta del caché
        cached_response = get_cached_data(cache_key)
        
        if cached_response:
            # Crear respuesta HTTP desde el caché
            from django.http import HttpResponse
            response = HttpResponse(
                cached_response['content'],
                content_type=cached_response.get('content_type', 'text/html'),
                status=cached_response.get('status_code', 200)
            )
            
            # Agregar headers del caché
            for header, value in cached_response.get('headers', {}).items():
                response[header] = value
            
            # Agregar header indicando que viene del caché
            response['X-Cache'] = 'HIT'
            
            return response
        
        return None
    
    def process_response(self, request, response):
        """
        Almacena la respuesta en caché si es apropiado.
        """
        # Solo cachear respuestas exitosas
        if response.status_code != 200:
            return response
        
        # No cachear para usuarios autenticados en ciertas páginas
        # Solo verificar si el usuario está disponible
        if (hasattr(request, 'user') and 
            request.user and
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated and 
            any(request.path.startswith(path) for path in ['/dashboard/', '/admin/'])):
            return response
        
        # No cachear rutas específicas
        if any(request.path.startswith(path) for path in self.no_cache_paths):
            return response
        
        # No cachear solicitudes POST
        if request.method != 'GET':
            return response
        
        # Determinar tiempo de caché
        cache_timeout = self._get_cache_timeout(request.path)
        
        if cache_timeout > 0:
            # Generar clave de caché
            cache_key = self._get_cache_key(request)
            
            # Preparar datos para caché
            cache_data = {
                'content': response.content.decode('utf-8'),
                'content_type': response.get('Content-Type', 'text/html'),
                'status_code': response.status_code,
                'headers': dict(response.items()),
                'timestamp': time.time(),
            }
            
            # Almacenar en caché
            cache_page_data(cache_key, cache_data, cache_timeout)
        
        # Agregar header indicando que no viene del caché
        response['X-Cache'] = 'MISS'
        
        return response
    
    def _get_cache_key(self, request):
        """
        Genera una clave de caché única para la solicitud.
        """
        # Incluir parámetros de consulta relevantes
        query_params = []
        for key in ['page', 'q', 'sort_by']:
            if key in request.GET:
                query_params.append(f"{key}:{request.GET[key]}")
        
        # Incluir estado de autenticación de forma segura
        auth_state = 'anon'
        if (hasattr(request, 'user') and 
            request.user and
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated):
            auth_state = 'auth'
        
        # Crear clave única
        key_parts = [
            request.path,
            auth_state,
            ':'.join(query_params) if query_params else 'no_params'
        ]
        
        return make_cache_key('page', ':'.join(key_parts))
    
    def _get_cache_timeout(self, path):
        """
        Determina el tiempo de caché apropiado para una ruta.
        """
        for route, timeout in self.cache_config.items():
            if path.startswith(route):
                return timeout
        
        # Tiempo por defecto
        return 0  # No cachear por defecto


class APIResponseCacheMiddleware(MiddlewareMixin):
    """
    Middleware específico para cachear respuestas de API.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.api_cache_timeout = 60  # 1 minuto para API
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Verifica si existe una respuesta de API cacheada.
        """
        # Solo para rutas de API
        if not request.path.startswith('/api/'):
            return None
        
        # Solo para solicitudes GET
        if request.method != 'GET':
            return None
        
        # Generar clave de caché
        cache_key = self._get_api_cache_key(request)
        
        # Intentar obtener respuesta del caché
        cached_data = get_cached_data(cache_key)
        
        if cached_data:
            from django.http import JsonResponse
            response = JsonResponse(cached_data['data'], status=cached_data['status'])
            response['X-Cache'] = 'HIT'
            response['Content-Type'] = 'application/json'
            return response
        
        return None
    
    def process_response(self, request, response):
        """
        Almacena respuestas de API en caché.
        """
        # Solo para rutas de API
        if not request.path.startswith('/api/'):
            return response
        
        # Solo para solicitudes GET exitosas
        if request.method != 'GET' or response.status_code != 200:
            return response
        
        # Solo para respuestas JSON
        if not response.get('Content-Type', '').startswith('application/json'):
            return response
        
        try:
            # Generar clave de caché
            cache_key = self._get_api_cache_key(request)
            
            # Preparar datos para caché
            import json
            cache_data = {
                'data': json.loads(response.content.decode('utf-8')),
                'status': response.status_code,
                'timestamp': time.time(),
            }
            
            # Almacenar en caché
            cache_page_data(cache_key, cache_data, self.api_cache_timeout)
            
            # Agregar header
            response['X-Cache'] = 'MISS'
            
        except Exception:
            # Si hay error, no cachear
            pass
        
        return response
    
    def _get_api_cache_key(self, request):
        """
        Genera clave de caché para API.
        """
        # Incluir todos los parámetros de consulta para API
        query_string = request.META.get('QUERY_STRING', '')
        
        # Incluir estado de autenticación de forma segura
        auth_state = 'anon'
        if (hasattr(request, 'user') and 
            request.user and
            hasattr(request.user, 'is_authenticated') and 
            request.user.is_authenticated):
            auth_state = f"user:{request.user.id}"
        
        return make_cache_key('api', request.path, auth_state, query_string)