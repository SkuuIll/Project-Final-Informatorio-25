"""
Utilidades para configurar y gestionar pgbouncer con Django.
"""

import logging
import os
import subprocess
import time
from django.conf import settings
from django.db import connections

logger = logging.getLogger('django.db.backends')

def configure_pgbouncer():
    """
    Configura las conexiones de base de datos para usar pgbouncer.
    Debe llamarse después de que se hayan definido las configuraciones de base de datos.
    """
    if not settings.DEBUG and getattr(settings, 'USE_PGBOUNCER', False):
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

def check_pgbouncer_status():
    """
    Verifica el estado de pgbouncer.
    Retorna True si pgbouncer está funcionando correctamente.
    """
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            # Consulta para verificar el estado de pgbouncer
            cursor.execute("SHOW POOLS")
            pools = cursor.fetchall()
            
            # Verificar que hay pools activos
            if pools:
                logger.info(f"pgbouncer está funcionando correctamente con {len(pools)} pools")
                return True
            else:
                logger.warning("pgbouncer está funcionando pero no hay pools activos")
                return False
    except Exception as e:
        logger.error(f"Error al verificar el estado de pgbouncer: {str(e)}")
        return False

def get_pgbouncer_stats():
    """
    Obtiene estadísticas de pgbouncer.
    """
    try:
        from django.db import connection
        stats = {}
        
        with connection.cursor() as cursor:
            # Obtener estadísticas de pools
            cursor.execute("SHOW POOLS")
            columns = [col[0] for col in cursor.description]
            pools = [dict(zip(columns, row)) for row in cursor.fetchall()]
            stats['pools'] = pools
            
            # Obtener estadísticas de clientes
            cursor.execute("SHOW CLIENTS")
            columns = [col[0] for col in cursor.description]
            clients = [dict(zip(columns, row)) for row in cursor.fetchall()]
            stats['clients'] = clients
            
            # Obtener estadísticas de servidores
            cursor.execute("SHOW SERVERS")
            columns = [col[0] for col in cursor.description]
            servers = [dict(zip(columns, row)) for row in cursor.fetchall()]
            stats['servers'] = servers
            
            # Obtener estadísticas generales
            cursor.execute("SHOW STATS")
            columns = [col[0] for col in cursor.description]
            general_stats = [dict(zip(columns, row)) for row in cursor.fetchall()]
            stats['stats'] = general_stats
            
        return stats
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de pgbouncer: {str(e)}")
        return None

def setup_pgbouncer_for_docker():
    """
    Configura pgbouncer para un entorno Docker.
    Crea el archivo de configuración necesario.
    """
    if not os.environ.get('PGBOUNCER_ENABLED'):
        return
    
    config_dir = '/etc/pgbouncer'
    config_file = os.path.join(config_dir, 'pgbouncer.ini')
    
    # Crear directorio si no existe
    os.makedirs(config_dir, exist_ok=True)
    
    # Obtener configuración de la base de datos
    db_name = os.environ.get('POSTGRES_DB', 'devblog')
    db_user = os.environ.get('POSTGRES_USER', 'postgres')
    db_password = os.environ.get('POSTGRES_PASSWORD', 'postgres')
    db_host = os.environ.get('POSTGRES_HOST', 'db')
    db_port = os.environ.get('POSTGRES_PORT', '5432')
    
    # Configuración de pgbouncer
    pgbouncer_config = f"""[databases]
{db_name} = host={db_host} port={db_port} dbname={db_name}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
logfile = /var/log/pgbouncer/pgbouncer.log
pidfile = /var/run/pgbouncer/pgbouncer.pid
admin_users = {db_user}
stats_users = {db_user}
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
max_db_connections = 50
max_user_connections = 50
server_reset_query = DISCARD ALL
server_check_delay = 30
server_check_query = SELECT 1
server_lifetime = 3600
server_idle_timeout = 600
client_idle_timeout = 600
"""
    
    # Escribir archivo de configuración
    with open(config_file, 'w') as f:
        f.write(pgbouncer_config)
    
    # Crear archivo de usuarios
    userlist_file = os.path.join(config_dir, 'userlist.txt')
    with open(userlist_file, 'w') as f:
        # El formato es: "username" "password"
        # Para PostgreSQL, la contraseña debe estar en formato md5
        # pero pgbouncer puede manejar contraseñas en texto plano
        f.write(f'"{db_user}" "{db_password}"\n')
    
    logger.info("Configuración de pgbouncer creada correctamente")

def start_pgbouncer():
    """
    Inicia el servicio pgbouncer.
    """
    try:
        # Verificar si pgbouncer ya está en ejecución
        result = subprocess.run(['pgrep', 'pgbouncer'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("pgbouncer ya está en ejecución")
            return True
        
        # Iniciar pgbouncer
        subprocess.run(['pgbouncer', '-d', '/etc/pgbouncer/pgbouncer.ini'])
        
        # Esperar a que pgbouncer esté listo
        time.sleep(2)
        
        logger.info("pgbouncer iniciado correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al iniciar pgbouncer: {str(e)}")
        return False

def stop_pgbouncer():
    """
    Detiene el servicio pgbouncer.
    """
    try:
        # Verificar si pgbouncer está en ejecución
        result = subprocess.run(['pgrep', 'pgbouncer'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.info("pgbouncer no está en ejecución")
            return True
        
        # Detener pgbouncer
        subprocess.run(['pkill', 'pgbouncer'])
        
        logger.info("pgbouncer detenido correctamente")
        return True
    except Exception as e:
        logger.error(f"Error al detener pgbouncer: {str(e)}")
        return False

def restart_pgbouncer():
    """
    Reinicia el servicio pgbouncer.
    """
    stop_pgbouncer()
    time.sleep(1)
    return start_pgbouncer()

def configure_pgbouncer_for_production():
    """
    Configura pgbouncer para un entorno de producción.
    """
    if settings.DEBUG:
        logger.info("No se configura pgbouncer en modo DEBUG")
        return
    
    # Verificar si pgbouncer está instalado
    try:
        result = subprocess.run(['which', 'pgbouncer'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("pgbouncer no está instalado en el sistema")
            return
    except Exception:
        logger.warning("No se pudo verificar si pgbouncer está instalado")
        return
    
    # Configurar pgbouncer
    setup_pgbouncer_for_docker()
    
    # Iniciar pgbouncer si está habilitado
    if os.environ.get('PGBOUNCER_ENABLED', '').lower() in ('true', '1', 't'):
        start_pgbouncer()

def update_pgbouncer_config(max_connections=None, pool_size=None):
    """
    Actualiza la configuración de pgbouncer.
    
    Args:
        max_connections: Número máximo de conexiones de cliente
        pool_size: Tamaño del pool por defecto
    """
    if not os.path.exists('/etc/pgbouncer/pgbouncer.ini'):
        logger.warning("No se encontró el archivo de configuración de pgbouncer")
        return False
    
    try:
        # Leer configuración actual
        with open('/etc/pgbouncer/pgbouncer.ini', 'r') as f:
            config = f.read()
        
        # Actualizar configuración
        if max_connections:
            config = config.replace(
                'max_client_conn = 100',
                f'max_client_conn = {max_connections}'
            )
        
        if pool_size:
            config = config.replace(
                'default_pool_size = 20',
                f'default_pool_size = {pool_size}'
            )
        
        # Escribir configuración actualizada
        with open('/etc/pgbouncer/pgbouncer.ini', 'w') as f:
            f.write(config)
        
        logger.info("Configuración de pgbouncer actualizada correctamente")
        
        # Reiniciar pgbouncer para aplicar cambios
        restart_pgbouncer()
        
        return True
    except Exception as e:
        logger.error(f"Error al actualizar la configuración de pgbouncer: {str(e)}")
        return False