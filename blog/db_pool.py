"""
Database connection pooling configuration for improved performance.
"""
import os
import logging
from django.conf import settings

logger = logging.getLogger('django.db.backends')

def get_database_config():
    """
    Get database configuration with connection pooling.
    Uses pgbouncer-style connection pooling for PostgreSQL.
    """
    
    # Base database configuration
    database_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'devblog'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': int(os.getenv('DB_MAX_CONNS', '20')),
            'OPTIONS': {
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
            }
        },
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '300')),  # 5 minutes
    }
    
    # Add connection pooling options for production
    if not settings.DEBUG:
        database_config['OPTIONS'].update({
            'CONN_HEALTH_CHECKS': True,
            'CONN_MAX_AGE': 300,  # 5 minutes
            'OPTIONS': {
                'MAX_CONNS': 20,
                'MIN_CONNS': 5,
                'application_name': 'devblog_app',
                'connect_timeout': 10,
                'options': '-c default_transaction_isolation=read_committed'
            }
        })
    
    return database_config


# PgBouncer configuration template
PGBOUNCER_CONFIG = """
[databases]
devblog = host={host} port={port} dbname={dbname} user={user} password={password}

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Connection pooling settings
pool_mode = transaction
max_client_conn = 100
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 5

# Server connection settings
server_reset_query = DISCARD ALL
server_check_query = SELECT 1
server_check_delay = 30
max_db_connections = 50
max_user_connections = 50

# Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1

# Timeouts
server_lifetime = 3600
server_idle_timeout = 600
client_idle_timeout = 0
query_timeout = 0
query_wait_timeout = 120
client_login_timeout = 60
autodb_idle_timeout = 3600
"""


def generate_pgbouncer_config():
    """Generate PgBouncer configuration file."""
    config = PGBOUNCER_CONFIG.format(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        dbname=os.getenv('DB_NAME', 'devblog'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )
    
    return config


def setup_pgbouncer_for_docker():
    """
    Configure pgbouncer for Docker environment.
    Creates necessary configuration files and directories.
    """
    import os
    
    # Check if pgbouncer is enabled
    if not os.environ.get('PGBOUNCER_ENABLED', '').lower() in ('true', '1', 't'):
        logger.info("PgBouncer not enabled, skipping configuration")
        return
    
    logger.info("Setting up PgBouncer for Docker environment")
    
    # Create configuration directory
    config_dir = '/etc/pgbouncer'
    os.makedirs(config_dir, exist_ok=True)
    
    # Create log directory
    log_dir = '/var/log/pgbouncer'
    os.makedirs(log_dir, exist_ok=True)
    
    # Create run directory
    run_dir = '/var/run/pgbouncer'
    os.makedirs(run_dir, exist_ok=True)
    
    # Generate and write configuration
    config = generate_pgbouncer_config()
    with open(os.path.join(config_dir, 'pgbouncer.ini'), 'w') as f:
        f.write(config)
    
    # Create userlist file
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    
    with open(os.path.join(config_dir, 'userlist.txt'), 'w') as f:
        f.write(f'"{db_user}" "{db_password}"\n')
    
    logger.info("PgBouncer configuration completed")


def configure_connection_pooling():
    """
    Configure database connection pooling settings.
    Should be called after Django settings are loaded.
    """
    if not settings.DEBUG:
        # Set connection pooling parameters
        for db_name, db_config in settings.DATABASES.items():
            if db_config['ENGINE'] == 'django.db.backends.postgresql':
                # Set connection pooling parameters
                db_config.setdefault('CONN_MAX_AGE', 60)  # Keep connections open for 60 seconds
                db_config.setdefault('CONN_HEALTH_CHECKS', True)
                
                # Set options for better connection handling
                db_config.setdefault('OPTIONS', {})
                db_config['OPTIONS'].update({
                    'connect_timeout': 10,
                    'application_name': 'devblog',
                })
                
                logger.info(f"Configured connection pooling for database '{db_name}'")
                
        # Check if pgbouncer is enabled
        if getattr(settings, 'USE_PGBOUNCER', False):
            for db_name, db_config in settings.DATABASES.items():
                if db_config['ENGINE'] == 'django.db.backends.postgresql':
                    # Configure for pgbouncer
                    db_config.setdefault('OPTIONS', {})
                    db_config['OPTIONS']['prepared_statements'] = False
                    
                    logger.info(f"Configured pgbouncer for database '{db_name}'")