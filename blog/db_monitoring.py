import logging
import time
from django.db import connection
from django.conf import settings

logger = logging.getLogger('django.db.backends')

class QueryMonitoringMiddleware:
    """
    Middleware para monitorear consultas lentas y problemas N+1.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 100)
        self.query_count_threshold = getattr(settings, 'QUERY_COUNT_THRESHOLD', 20)
    
    def __call__(self, request):
        # Inicializar contadores
        start_queries = len(connection.queries)
        start_time = time.time()
        
        # Procesar la solicitud
        response = self.get_response(request)
        
        # Solo monitorear en DEBUG o si se ha configurado explícitamente
        if settings.DEBUG or getattr(settings, 'MONITOR_DB_QUERIES', False):
            # Calcular estadísticas
            end_time = time.time()
            end_queries = len(connection.queries)
            
            duration = (end_time - start_time) * 1000  # ms
            query_count = end_queries - start_queries
            
            # Registrar información básica
            request_path = request.path
            request_method = request.method
            user_id = getattr(request.user, 'id', None)
            
            # Detectar posibles problemas N+1
            if query_count > self.query_count_threshold:
                logger.warning(
                    f"Posible problema N+1 detectado: {query_count} consultas para {request_method} {request_path}",
                    extra={
                        'request_path': request_path,
                        'request_method': request_method,
                        'query_count': query_count,
                        'duration_ms': duration,
                        'user_id': user_id,
                    }
                )
                
                # Registrar las consultas para diagnóstico
                query_details = []
                for i, query in enumerate(connection.queries[start_queries:end_queries]):
                    query_time = float(query.get('time', 0)) * 1000  # ms
                    query_sql = query.get('sql', '')
                    
                    # Registrar consultas lentas individualmente
                    if query_time > self.slow_query_threshold:
                        logger.warning(
                            f"Consulta lenta ({query_time:.2f}ms): {query_sql[:200]}...",
                            extra={
                                'query_time_ms': query_time,
                                'query_sql': query_sql,
                                'request_path': request_path,
                            }
                        )
                    
                    query_details.append({
                        'index': i,
                        'time_ms': query_time,
                        'sql': query_sql[:500],  # Limitar longitud
                    })
                
                # Registrar detalles completos en nivel DEBUG
                logger.debug(
                    f"Detalles de consultas para {request_method} {request_path}",
                    extra={
                        'query_details': query_details,
                        'request_path': request_path,
                    }
                )
            
            # Registrar tiempo total si es lento
            if duration > self.slow_query_threshold * 2:  # Umbral más alto para el tiempo total
                logger.warning(
                    f"Solicitud lenta: {duration:.2f}ms con {query_count} consultas para {request_method} {request_path}",
                    extra={
                        'request_path': request_path,
                        'request_method': request_method,
                        'duration_ms': duration,
                        'query_count': query_count,
                        'user_id': user_id,
                    }
                )
        
        return response


class QueryCountMonitor:
    """
    Utilidad para monitorear el número de consultas en un bloque de código.
    
    Uso:
    ```
    with QueryCountMonitor('Nombre de operación'):
        # Código que ejecuta consultas
    ```
    """
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_queries = 0
        self.start_time = 0
    
    def __enter__(self):
        self.start_queries = len(connection.queries)
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        end_queries = len(connection.queries)
        
        duration = (end_time - self.start_time) * 1000  # ms
        query_count = end_queries - self.start_queries
        
        logger.info(
            f"[QueryMonitor] {self.operation_name}: {query_count} consultas en {duration:.2f}ms",
            extra={
                'operation': self.operation_name,
                'query_count': query_count,
                'duration_ms': duration,
            }
        )
        
        # Registrar consultas individuales en nivel DEBUG
        for i, query in enumerate(connection.queries[self.start_queries:end_queries]):
            query_time = float(query.get('time', 0)) * 1000  # ms
            query_sql = query.get('sql', '')
            
            logger.debug(
                f"[QueryMonitor] {self.operation_name} - Consulta {i+1}: {query_time:.2f}ms",
                extra={
                    'operation': self.operation_name,
                    'query_index': i,
                    'query_time_ms': query_time,
                    'query_sql': query_sql,
                }
            )


def setup_pgbouncer():
    """
    Configura la conexión a PostgreSQL para usar pgbouncer.
    Debe llamarse en settings.py después de definir DATABASES.
    """
    if not settings.DEBUG and getattr(settings, 'USE_PGBOUNCER', False):
        # Configuración para pgbouncer
        for db_name, db_config in settings.DATABASES.items():
            if db_config['ENGINE'] == 'django.db.backends.postgresql':
                # Configurar opciones para pgbouncer
                db_config.setdefault('OPTIONS', {})
                
                # Usar prepared statements = False para pgbouncer en modo transaction
                db_config['OPTIONS']['prepared_statements'] = False
                
                # Configurar pool_timeout
                db_config['OPTIONS']['connect_timeout'] = 3
                
                # Configurar max_age para conexiones
                db_config['CONN_MAX_AGE'] = 60  # 60 segundos
                
                logger.info(f"Configurado pgbouncer para base de datos '{db_name}'")