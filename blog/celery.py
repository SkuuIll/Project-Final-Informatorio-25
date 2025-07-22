"""
Configuración de Celery para tareas en background.
"""

import os
import logging
from celery import Celery
from celery.signals import task_failure, task_success, task_retry, worker_ready
from django.conf import settings

logger = logging.getLogger('celery')

# Establecer la variable de entorno para configuraciones de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')

# Crear instancia de Celery
app = Celery('blog')

# Cargar configuración desde settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubrir tareas automáticamente
app.autodiscover_tasks()

# Configuración de colas
app.conf.task_routes = {
    'posts.tasks.generate_ai_content': {'queue': 'ai_processing'},
    'posts.tasks.optimize_images': {'queue': 'media_processing'},
    'accounts.tasks.send_notifications': {'queue': 'notifications'},
    'blog.tasks.maintenance_tasks': {'queue': 'maintenance'},
}

# Configuración de reintentos
app.conf.task_acks_late = True  # Confirmar tareas después de completarlas
app.conf.task_reject_on_worker_lost = True  # Rechazar tareas si el worker se pierde
app.conf.task_default_retry_delay = 60  # 1 minuto entre reintentos
app.conf.task_max_retries = 3  # Máximo 3 reintentos

# Configuración de monitoreo
app.conf.worker_send_task_events = True
app.conf.task_send_sent_event = True

# Configuración de serialización
app.conf.accept_content = ['json']
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'

# Configuración de resultados
app.conf.result_backend = settings.CELERY_RESULT_BACKEND
app.conf.result_expires = 60 * 60 * 24  # 24 horas

# Configuración de tareas periódicas
app.conf.beat_schedule = {
    'cleanup-old-notifications': {
        'task': 'accounts.tasks.cleanup_old_notifications',
        'schedule': 60 * 60 * 24,  # Cada 24 horas
        'kwargs': {'days': 30},  # Eliminar notificaciones de más de 30 días
    },
    'update-post-stats': {
        'task': 'posts.tasks.update_post_stats',
        'schedule': 60 * 15,  # Cada 15 minutos
    },
    'optimize-database': {
        'task': 'blog.tasks.optimize_database',
        'schedule': 60 * 60 * 24 * 7,  # Cada semana
    },
}


@task_failure.connect
def handle_task_failure(sender=None, task_id=None, exception=None, args=None, kwargs=None, **kw):
    """
    Manejador para fallos de tareas.
    """
    logger.error(
        f"Tarea fallida: {sender.name}",
        extra={
            'task_id': task_id,
            'exception': str(exception),
            'args': args,
            'kwargs': kwargs,
        },
        exc_info=exception,
    )


@task_success.connect
def handle_task_success(sender=None, result=None, **kwargs):
    """
    Manejador para tareas exitosas.
    """
    logger.info(
        f"Tarea completada: {sender.name}",
        extra={
            'task_id': kwargs.get('task_id'),
            'result': str(result)[:100] if result else None,
        }
    )


@task_retry.connect
def handle_task_retry(sender=None, request=None, reason=None, **kwargs):
    """
    Manejador para reintentos de tareas.
    """
    logger.warning(
        f"Reintentando tarea: {sender.name}",
        extra={
            'task_id': request.id,
            'reason': str(reason),
            'retries': request.retries,
            'max_retries': sender.max_retries,
        }
    )


@worker_ready.connect
def on_worker_ready(**kwargs):
    """
    Manejador para cuando el worker está listo.
    """
    logger.info("Worker de Celery iniciado y listo para procesar tareas")


@app.task(bind=True)
def debug_task(self):
    """
    Tarea de prueba para verificar que Celery está funcionando.
    """
    logger.info(f"Request: {self.request!r}")
    return "Celery está funcionando correctamente"