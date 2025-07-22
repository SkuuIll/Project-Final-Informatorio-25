"""
Configuración de PgBouncer para la aplicación DevBlog.
"""
import os
import logging
from django.conf import settings

logger = logging.getLogger('django.db.backends')

def configure_pgbouncer_for_databases():
    """
    Configura las bases de datos para usar PgBouncer.
    Esta función debe ser llamada después de que se hayan definido las configuraciones de base de datos.
    """
    # Verificar si estamos en modo DEBUG
    if 'settings' in globals() and settings.DEBUG:
        logger.info("No se configura PgBouncer en modo DEBUG")
        return
    
    # Verificar si PgBouncer está habilitado
    use_pgbouncer = os.environ.get('USE_PGBOUNCER', 'False').lower() in ('true', '1', 't')
    if not use_pgbouncer:
        return
    
    # Obtener configuración de PgBouncer
    pgbouncer_host = os.environ.get('PGBOUNCER_HOST', 'localhost')
    pgbouncer_port = os.environ.get('PGBOUNCER_PORT', '6432')
    
    # Configurar bases de datos para usar PgBouncer
    if 'settings' in globals() and hasattr(settings, 'DATABASES'):
        for db_name, db_config in settings.DATABASES.items():
            if db_config['ENGINE'] == 'django.db.backends.postgresql':
                # Configurar para PgBouncer
                db_config.setdefault('OPTIONS', {})
                
                # Usar prepared statements = False para PgBouncer en modo transaction
                db_config['OPTIONS']['prepared_statements'] = False
                
                # Configurar timeout de conexión
                db_config['OPTIONS']['connect_timeout'] = 3
                
                # Configurar max_age para conexiones
                db_config['CONN_MAX_AGE'] = 60  # 60 segundos
                
                # Cambiar host y puerto para usar PgBouncer
                db_config['HOST'] = pgbouncer_host
                db_config['PORT'] = pgbouncer_port
                
                logger.info(f"Configurado PgBouncer para base de datos '{db_name}'")
    else:
        logger.warning("No se pudo configurar PgBouncer: settings.DATABASES no está disponible")