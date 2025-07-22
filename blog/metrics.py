"""
Configuración de métricas con Prometheus para monitoreo.
"""

import time
import logging
from prometheus_client import Counter, Histogram, Gauge, Summary
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.metrics')

# Contadores
REQUEST_COUNTER = Counter(
    'django_http_requests_total',
    'Total de solicitudes HTTP',
    ['method', 'endpoint', 'status']
)

USER_COUNTER = Counter(
    'django_user_actions_total',
    'Total de acciones de usuario',
    ['action_type', 'user_type']
)

ERROR_COUNTER = Counter(
    'django_errors_total',
    'Total de errores',
    ['error_type', 'endpoint']
)

# Histogramas
REQUEST_LATENCY = Histogram(
    'django_http_request_duration_seconds',
    'Duración de solicitudes HTTP',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

DB_QUERY_LATENCY = Histogram(
    'django_db_query_duration_seconds',
    'Duración de consultas de base de datos',
    ['query_type'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

# Gauges
ACTIVE_USERS = Gauge(
    'django_active_users',
    'Usuarios activos actualmente',
    ['authenticated']
)

ACTIVE_REQUESTS = Gauge(
    'django_active_requests',
    'Solicitudes activas actualmente',
    ['method']
)

# Summaries
RESPONSE_SIZE = Summary(
    'django_http_response_size_bytes',
    'Tamaño de respuestas HTTP',
    ['method', 'endpoint']
)


class PrometheusMiddleware(MiddlewareMixin):
    """
    Middleware para recolectar métricas de Prometheus.
    """
    
    def process_request(self, request):
        """
        Procesa la solicitud entrante.
        """
        request.start_time = time.time()
        
        # Incrementar contador de solicitudes activas
        method = request.method
        ACTIVE_REQUESTS.labels(method=method).inc()
        
        # Registrar usuarios activos
        is_authenticated = request.user.is_authenticated
        ACTIVE_USERS.labels(authenticated=str(is_authenticated)).inc()
    
    def process_response(self, request, response):
        """
        Procesa la respuesta saliente.
        """
        # Decrementar contador de solicitudes activas
        method = request.method
        ACTIVE_REQUESTS.labels(method=method).dec()
        
        # Decrementar contador de usuarios activos
        is_authenticated = getattr(request, 'user', None) and request.user.is_authenticated
        ACTIVE_USERS.labels(authenticated=str(is_authenticated)).dec()
        
        # Calcular duración
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Determinar endpoint para las métricas
            if hasattr(request, 'resolver_match') and request.resolver_match:
                endpoint = request.resolver_match.view_name
            else:
                endpoint = request.path
            
            # Registrar latencia
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
            # Registrar contador de solicitudes
            REQUEST_COUNTER.labels(
                method=request.method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            # Registrar tamaño de respuesta
            if hasattr(response, 'content'):
                RESPONSE_SIZE.labels(
                    method=request.method,
                    endpoint=endpoint
                ).observe(len(response.content))
        
        return response
    
    def process_exception(self, request, exception):
        """
        Procesa excepciones.
        """
        # Determinar endpoint para las métricas
        if hasattr(request, 'resolver_match') and request.resolver_match:
            endpoint = request.resolver_match.view_name
        else:
            endpoint = request.path
        
        # Registrar error
        ERROR_COUNTER.labels(
            error_type=type(exception).__name__,
            endpoint=endpoint
        ).inc()


# Funciones de utilidad para registrar métricas personalizadas

def track_user_action(action_type, user=None):
    """
    Registra una acción de usuario.
    
    Args:
        action_type: Tipo de acción (login, logout, post_create, etc.)
        user: Usuario que realiza la acción
    """
    user_type = 'authenticated' if user and user.is_authenticated else 'anonymous'
    USER_COUNTER.labels(
        action_type=action_type,
        user_type=user_type
    ).inc()

def track_db_query(query_type, duration):
    """
    Registra una consulta de base de datos.
    
    Args:
        query_type: Tipo de consulta (select, insert, update, delete)
        duration: Duración en segundos
    """
    DB_QUERY_LATENCY.labels(
        query_type=query_type
    ).observe(duration)

def track_error(error_type, endpoint=None):
    """
    Registra un error.
    
    Args:
        error_type: Tipo de error
        endpoint: Endpoint donde ocurrió el error
    """
    ERROR_COUNTER.labels(
        error_type=error_type,
        endpoint=endpoint or 'unknown'
    ).inc()