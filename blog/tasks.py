"""
Tareas de Celery para mantenimiento del sistema.
"""

import logging
from celery import shared_task
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('celery')

@shared_task(
    name='blog.tasks.optimize_database',
    bind=True,
    max_retries=2,
    default_retry_delay=300,  # 5 minutos
    acks_late=True,
    ignore_result=False,
)
def optimize_database(self):
    """
    Optimiza la base de datos ejecutando VACUUM y ANALYZE en PostgreSQL.
    """
    try:
        with connection.cursor() as cursor:
            # Verificar si estamos usando PostgreSQL
            if connection.vendor == 'postgresql':
                logger.info("Iniciando optimización de base de datos PostgreSQL")
                
                # Obtener tablas
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    # VACUUM ANALYZE para cada tabla
                    logger.info(f"Optimizando tabla: {table}")
                    cursor.execute(f'VACUUM ANALYZE "{table}"')
                
                logger.info(f"Optimización de base de datos completada: {len(tables)} tablas procesadas")
                return f"Optimización completada: {len(tables)} tablas"
            else:
                logger.info(f"Optimización de base de datos no soportada para {connection.vendor}")
                return f"Optimización no soportada para {connection.vendor}"
    except Exception as e:
        logger.error(f"Error en optimización de base de datos: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='blog.tasks.clear_expired_sessions',
    bind=True,
    max_retries=1,
    default_retry_delay=60,  # 1 minuto
)
def clear_expired_sessions(self):
    """
    Elimina sesiones expiradas de la base de datos.
    """
    try:
        from django.contrib.sessions.models import Session
        
        # Eliminar sesiones expiradas
        expired = Session.objects.filter(expire_date__lt=timezone.now())
        count = expired.count()
        expired.delete()
        
        logger.info(f"Sesiones expiradas eliminadas: {count}")
        return f"Sesiones eliminadas: {count}"
    except Exception as e:
        logger.error(f"Error al limpiar sesiones: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='blog.tasks.clear_cache',
    bind=True,
)
def clear_cache(self, pattern=None):
    """
    Limpia la caché, opcionalmente por patrón.
    """
    try:
        if pattern:
            # Limpiar por patrón (requiere backend de Redis)
            if hasattr(cache, 'delete_pattern'):
                count = cache.delete_pattern(pattern)
                logger.info(f"Caché limpiada por patrón '{pattern}': {count} claves")
                return f"Caché limpiada: {count} claves"
            else:
                logger.warning("Limpieza por patrón no soportada por el backend de caché")
                return "Limpieza por patrón no soportada"
        else:
            # Limpiar toda la caché
            cache.clear()
            logger.info("Caché completamente limpiada")
            return "Caché completamente limpiada"
    except Exception as e:
        logger.error(f"Error al limpiar caché: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"


@shared_task(
    name='blog.tasks.cleanup_old_files',
    bind=True,
    max_retries=2,
)
def cleanup_old_files(self, days=30):
    """
    Elimina archivos temporales antiguos.
    """
    import os
    from django.conf import settings
    
    try:
        # Directorios a limpiar
        dirs_to_clean = [
            os.path.join(settings.MEDIA_ROOT, 'temp'),
            os.path.join(settings.MEDIA_ROOT, 'uploads', 'temp'),
        ]
        
        cutoff_date = timezone.now() - timedelta(days=days)
        total_removed = 0
        
        for directory in dirs_to_clean:
            if not os.path.exists(directory):
                continue
                
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_modified = timezone.datetime.fromtimestamp(
                        os.path.getmtime(file_path), 
                        tz=timezone.get_current_timezone()
                    )
                    
                    if file_modified < cutoff_date:
                        os.remove(file_path)
                        total_removed += 1
        
        logger.info(f"Archivos temporales eliminados: {total_removed}")
        return f"Archivos eliminados: {total_removed}"
    except Exception as e:
        logger.error(f"Error al limpiar archivos: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='blog.tasks.health_check',
)
def health_check():
    """
    Verifica la salud del sistema.
    """
    health_status = {
        'database': False,
        'cache': False,
        'storage': False,
        'celery': True,  # Si esta tarea se ejecuta, Celery está funcionando
    }
    
    # Verificar base de datos
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['database'] = cursor.fetchone()[0] == 1
    except Exception as e:
        logger.error(f"Error en health check de base de datos: {str(e)}")
    
    # Verificar caché
    try:
        cache_key = 'health_check'
        cache.set(cache_key, 'ok', 10)
        health_status['cache'] = cache.get(cache_key) == 'ok'
    except Exception as e:
        logger.error(f"Error en health check de caché: {str(e)}")
    
    # Verificar almacenamiento
    try:
        import tempfile
        import os
        from django.core.files.storage import default_storage
        from django.core.files.base import ContentFile
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(b'health check')
        temp_file.close()
        
        # Verificar que se puede leer
        with open(temp_file.name, 'rb') as f:
            content = f.read()
            health_status['storage'] = content == b'health check'
        
        # Limpiar
        os.unlink(temp_file.name)
    except Exception as e:
        logger.error(f"Error en health check de almacenamiento: {str(e)}")
    
    # Registrar resultado
    all_healthy = all(health_status.values())
    if all_healthy:
        logger.info("Health check completado: todos los sistemas funcionando")
    else:
        logger.warning(
            f"Health check completado con problemas: {health_status}",
            extra={'health_status': health_status}
        )
    
    return health_status