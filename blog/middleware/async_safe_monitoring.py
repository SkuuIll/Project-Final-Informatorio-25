"""
Middleware de monitoreo compatible con async/sync.
"""
import time
import logging
from django.db import connection
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('blog.db_monitoring')

class AsyncSafeQueryMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware de monitoreo de consultas compatible con async/sync.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 100)
        self.query_count_threshold = getattr(settings, 'QUERY_COUNT_THRESHOLD', 20)
        super().__init__(get_response)
        
    def process_request(self, request):
        """Inicializar contadores al inicio de la solicitud."""
        request._monitoring_start_time = time.time()
        request._monitoring_start_queries = len(connection.queries)
        return None
        
    def process_response(self, request, response):
        """Procesar estadísticas al final de la solicitud."""
        # Solo monitorear si está habilitado
        if not (settings.DEBUG or getattr(settings, 'MONITOR_DB_QUERIES', False)):
            return response
            
        # Verificar que tenemos los datos de inicio
        if not hasattr(request, '_monitoring_start_time'):
            return response
            
        # Ignorar solicitudes a archivos estáticos
        if request.path.startswith(('/static/', '/media/', '/favicon.ico')):
            return response
            
        try:
            # Calcular estadísticas
            end_time = time.time()
            end_queries = len(connection.queries)
            
            duration = (end_time - request._monitoring_start_time) * 1000  # ms
            query_count = end_queries - request._monitoring_start_queries
            
            # Registrar información básica
            if query_count > 0:
                logger.info(
                    f"{query_count} consultas en {duration:.2f}ms para {request.method} {request.path}",
                    extra={
                        'request_path': request.path,
                        'request_method': request.method,
                        'query_count': query_count,
                        'duration_ms': duration,
                        'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                    }
                )
            
            # Detectar posibles problemas N+1
            if query_count > self.query_count_threshold:
                logger.warning(
                    f"Posible problema N+1: {query_count} consultas para {request.method} {request.path}",
                    extra={
                        'request_path': request.path,
                        'request_method': request.method,
                        'query_count': query_count,
                        'duration_ms': duration,
                    }
                )
                
        except Exception as e:
            # No fallar si hay problemas con el monitoreo
            logger.error(f"Error en monitoreo de consultas: {e}")
            
        return response