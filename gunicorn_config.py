#!/usr/bin/env python3
"""
Configuración optimizada de Gunicorn para el servidor de producción.
Diseñada para manejar eficientemente la generación de contenido con IA
y evitar problemas de memoria.
"""

import multiprocessing
import os

# ================================
# CONFIGURACIÓN DE WORKERS
# ================================

# Número de workers basado en CPU pero limitado para evitar problemas de memoria
# Fórmula: (2 x CPU cores) + 1, pero máximo 3 para evitar sobrecarga de memoria
cpu_count = multiprocessing.cpu_count()
workers = min((cpu_count * 2) + 1, 3)

# Tipo de worker - sync es más estable para operaciones de IA
worker_class = "sync"

# Conexiones por worker
worker_connections = 1000

# ================================
# GESTIÓN DE MEMORIA
# ================================

# Reiniciar worker después de N requests para evitar memory leaks
max_requests = 500  # Reducido para liberar memoria más frecuentemente
max_requests_jitter = 50  # Variación aleatoria para evitar reinicios simultáneos

# Precargar la aplicación para compartir memoria entre workers
preload_app = True

# ================================
# TIMEOUTS
# ================================

# Timeout más largo para operaciones de IA (2 minutos)
timeout = 120

# Timeout para workers silenciosos
graceful_timeout = 30

# Keepalive para conexiones persistentes
keepalive = 5

# ================================
# CONFIGURACIÓN DE RED
# ================================

# Bind a todas las interfaces en el puerto 8000
bind = "0.0.0.0:8000"

# Backlog de conexiones
backlog = 2048

# ================================
# LOGGING
# ================================

# Nivel de logging
loglevel = "info"

# Formato de logs
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Archivos de log
accesslog = "/app/logs/gunicorn_access.log"
errorlog = "/app/logs/gunicorn_error.log"

# Capturar salida de la aplicación
capture_output = True

# ================================
# CONFIGURACIÓN DE PROCESO
# ================================

# Nombre del proceso
proc_name = "devblog_gunicorn"

# Usuario y grupo (si se ejecuta como root)
# user = "app"
# group = "app"

# Directorio de trabajo
chdir = "/app"

# ================================
# HOOKS DE GUNICORN
# ================================

def when_ready(server):
    """Hook ejecutado cuando el servidor está listo."""
    server.log.info("Servidor Gunicorn iniciado correctamente")
    server.log.info(f"Workers configurados: {workers}")
    server.log.info(f"Timeout configurado: {timeout}s")

def worker_int(worker):
    """Hook ejecutado cuando un worker recibe SIGINT."""
    worker.log.info(f"Worker {worker.pid} recibió SIGINT - terminando gracefully")

def pre_fork(server, worker):
    """Hook ejecutado antes de hacer fork de un worker."""
    server.log.info(f"Iniciando worker {worker.age}")

def post_fork(server, worker):
    """Hook ejecutado después de hacer fork de un worker."""
    server.log.info(f"Worker {worker.pid} iniciado correctamente")
    
    # Configurar límites de memoria para el worker
    try:
        import resource
        # Límite de memoria virtual: 1.5GB por worker
        resource.setrlimit(resource.RLIMIT_AS, (1536 * 1024 * 1024, 1536 * 1024 * 1024))
        server.log.info(f"Límite de memoria configurado para worker {worker.pid}")
    except Exception as e:
        server.log.warning(f"No se pudo configurar límite de memoria: {e}")

def worker_abort(worker):
    """Hook ejecutado cuando un worker es abortado."""
    worker.log.error(f"Worker {worker.pid} fue abortado - posible problema de memoria")

def pre_exec(server):
    """Hook ejecutado antes de exec."""
    server.log.info("Reiniciando servidor Gunicorn")

# ================================
# CONFIGURACIÓN ADICIONAL
# ================================

# Recargar automáticamente si cambian los archivos (solo desarrollo)
reload = os.environ.get('GUNICORN_RELOAD', 'False').lower() == 'true'

# Directorio temporal
tmp_upload_dir = "/tmp"

# Configuración SSL (si es necesario)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"