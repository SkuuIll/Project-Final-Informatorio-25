"""
Middleware para monitoreo y optimización de consultas a la base de datos.
"""
import time
import logging
import json
from django.db import connection
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.db.backends')
monitoring_logger = logging.getLogger('blog.db_monitoring')

class QueryCountDebugMiddleware(MiddlewareMixin):
    """
    Middleware que cuenta y registra el número de consultas SQL ejecutadas en cada solicitud.
    Útil para detectar problemas N+1 y optimizar el rendimiento.
    """
    
    def process_request(self, request):
        request.start_time = time.time()
        request.start_queries = len(connection.queries)
        return None

    def process_response(self, request, response):
        if not hasattr(request, 'start_time'):
            return response
            
        # Solo monitorear si DEBUG está activado o se ha configurado explícitamente
        if not (settings.DEBUG or getattr(settings, 'MONITOR_DB_QUERIES', False)):
            return response
            
        total_time = time.time() - request.start_time
        total_queries = len(connection.queries) - request.start_queries
        
        # Ignorar solicitudes a archivos estáticos y otras rutas no relevantes
        if request.path.startswith(('/static/', '/media/', '/favicon.ico')):
            return response
            
        # Registrar información básica
        if total_queries > 0:
            query_info = {
                'path': request.path,
                'method': request.method,
                'query_count': total_queries,
                'time': total_time,
                'time_per_query': total_time / total_queries if total_queries > 0 else 0,
                'user_id': getattr(request.user, 'id', None),
            }
            
            # Detectar posibles problemas N+1
            query_threshold = getattr(settings, 'QUERY_COUNT_THRESHOLD', 20)
            if total_queries > query_threshold:
                monitoring_logger.warning(
                    f"Posible problema N+1: {total_queries} consultas en {request.path}",
                    extra=query_info
                )
                
                # En modo DEBUG, registrar todas las consultas para diagnóstico
                if settings.DEBUG:
                    queries_by_type = {}
                    for query in connection.queries[request.start_queries:]:
                        sql = query.get('sql', '')
                        sql_type = sql.split()[0].upper() if sql else 'UNKNOWN'
                        queries_by_type.setdefault(sql_type, 0)
                        queries_by_type[sql_type] += 1
                        
                    monitoring_logger.debug(
                        f"Desglose de consultas para {request.path}: {json.dumps(queries_by_type)}",
                        extra={'queries_by_type': queries_by_type, 'path': request.path}
                    )
            else:
                monitoring_logger.info(
                    f"Consultas para {request.path}: {total_queries} en {total_time:.2f}s",
                    extra=query_info
                )
                
        return response


class SlowQueryLogMiddleware(MiddlewareMixin):
    """
    Middleware que registra consultas SQL lentas.
    """
    
    def process_request(self, request):
        request.start_queries_slow = len(connection.queries)
        return None
        
    def process_response(self, request, response):
        if not hasattr(request, 'start_queries_slow'):
            return response
            
        # Solo monitorear si DEBUG está activado o se ha configurado explícitamente
        if not (settings.DEBUG or getattr(settings, 'MONITOR_DB_QUERIES', False)):
            return response
            
        # Umbral para considerar una consulta como lenta (en ms)
        slow_query_threshold = getattr(settings, 'SLOW_QUERY_THRESHOLD_MS', 100)
        
        # Analizar consultas lentas
        slow_queries = []
        for query in connection.queries[request.start_queries_slow:]:
            query_time = float(query.get('time', 0)) * 1000  # Convertir a ms
            if query_time > slow_query_threshold:
                slow_queries.append({
                    'sql': query.get('sql', ''),
                    'time': query_time,
                })
                
        # Registrar consultas lentas
        if slow_queries:
            for i, query in enumerate(slow_queries):
                monitoring_logger.warning(
                    f"Consulta lenta #{i+1} ({query['time']:.2f}ms): {query['sql'][:200]}...",
                    extra={
                        'path': request.path,
                        'method': request.method,
                        'query_time': query['time'],
                        'query_sql': query['sql'],
                        'user_id': getattr(request.user, 'id', None),
                    }
                )
                
        return response


class QueryMonitoringMiddleware:
    """
    Middleware completo para monitoreo de consultas SQL.
    Combina la detección de consultas lentas y problemas N+1.
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
            # Ignorar solicitudes a archivos estáticos y otras rutas no relevantes
            if request.path.startswith(('/static/', '/media/', '/favicon.ico')):
                return response
                
            # Calcular estadísticas
            end_time = time.time()
            end_queries = len(connection.queries)
            
            duration = (end_time - start_time) * 1000  # ms
            query_count = end_queries - start_queries
            
            # Registrar información básica
            request_path = request.path
            request_method = request.method
            user_id = getattr(request.user, 'id', None)
            
            # Registrar estadísticas generales
            if query_count > 0:
                monitoring_logger.info(
                    f"{query_count} consultas en {duration:.2f}ms para {request_method} {request_path}",
                    extra={
                        'request_path': request_path,
                        'request_method': request_method,
                        'query_count': query_count,
                        'duration_ms': duration,
                        'time_per_query': duration / query_count if query_count > 0 else 0,
                        'user_id': user_id,
                    }
                )
            
            # Detectar posibles problemas N+1
            if query_count > self.query_count_threshold:
                monitoring_logger.warning(
                    f"Posible problema N+1 detectado: {query_count} consultas para {request_method} {request_path}",
                    extra={
                        'request_path': request_path,
                        'request_method': request_method,
                        'query_count': query_count,
                        'duration_ms': duration,
                        'user_id': user_id,
                    }
                )
                
                # Analizar tipos de consultas para diagnóstico
                queries_by_type = {}
                for query in connection.queries[start_queries:end_queries]:
                    sql = query.get('sql', '')
                    sql_type = sql.split()[0].upper() if sql else 'UNKNOWN'
                    queries_by_type.setdefault(sql_type, 0)
                    queries_by_type[sql_type] += 1
                    
                monitoring_logger.debug(
                    f"Desglose de consultas para {request_path}: {json.dumps(queries_by_type)}",
                    extra={'queries_by_type': queries_by_type, 'path': request_path}
                )
                
            # Registrar consultas lentas
            slow_queries = []
            for i, query in enumerate(connection.queries[start_queries:end_queries]):
                query_time = float(query.get('time', 0)) * 1000  # ms
                query_sql = query.get('sql', '')
                
                # Registrar consultas lentas individualmente
                if query_time > self.slow_query_threshold:
                    monitoring_logger.warning(
                        f"Consulta lenta ({query_time:.2f}ms): {query_sql[:200]}...",
                        extra={
                            'query_time_ms': query_time,
                            'query_sql': query_sql,
                            'request_path': request_path,
                            'query_index': i,
                        }
                    )
                    
                    slow_queries.append({
                        'index': i,
                        'time_ms': query_time,
                        'sql': query_sql[:500],  # Limitar longitud
                    })
            
            # Registrar tiempo total si es lento
            if duration > self.slow_query_threshold * 2:  # Umbral más alto para el tiempo total
                monitoring_logger.warning(
                    f"Solicitud lenta: {duration:.2f}ms con {query_count} consultas para {request_method} {request_path}",
                    extra={
                        'request_path': request_path,
                        'request_method': request_method,
                        'duration_ms': duration,
                        'query_count': query_count,
                        'user_id': user_id,
                        'slow_queries_count': len(slow_queries),
                    }
                )
        
        return response