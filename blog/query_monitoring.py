"""
Módulo para monitoreo de consultas de base de datos.
"""
import time
import logging
import json
from django.db import connection, connections
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('django.db.backends')
monitoring_logger = logging.getLogger('blog.db_monitoring')

class ComprehensiveQueryMonitoringMiddleware(MiddlewareMixin):
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

def get_db_stats():
    """
    Obtiene estadísticas de la base de datos.
    """
    stats = {}
    
    for alias in connections:
        conn = connections[alias]
        stats[alias] = {
            'vendor': conn.vendor,
            'is_usable': conn.is_usable(),
        }
        
        # Estadísticas específicas para PostgreSQL
        if conn.vendor == 'postgresql':
            try:
                with conn.cursor() as cursor:
                    # Tamaño de la base de datos
                    cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                    stats[alias]['database_size'] = cursor.fetchone()[0]
                    
                    # Conexiones activas
                    cursor.execute("SELECT count(*) FROM pg_stat_activity")
                    stats[alias]['active_connections'] = cursor.fetchone()[0]
                    
                    # Estadísticas de tablas
                    cursor.execute("""
                        SELECT relname, n_live_tup, n_dead_tup
                        FROM pg_stat_user_tables
                        ORDER BY n_live_tup DESC
                        LIMIT 10
                    """)
                    stats[alias]['table_stats'] = [
                        {'table': row[0], 'live_rows': row[1], 'dead_rows': row[2]}
                        for row in cursor.fetchall()
                    ]
            except Exception as e:
                stats[alias]['stats_error'] = str(e)
    
    return stats