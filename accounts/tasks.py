"""
Tareas de Celery para la aplicación de accounts.
"""

import logging
import time
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.conf import settings
from datetime import timedelta
from .models import Notification, Profile

logger = logging.getLogger('celery')

@shared_task(
    name='accounts.tasks.send_email_notification',
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutos
    rate_limit='100/h',  # Limitar a 100 por hora
    queue='notifications',
)
def send_email_notification(self, user_id, subject, template, context=None, from_email=None):
    """
    Envía un email de notificación a un usuario.
    
    Args:
        user_id: ID del usuario
        subject: Asunto del email
        template: Plantilla HTML a usar
        context: Contexto para la plantilla
        from_email: Email remitente (opcional)
    """
    try:
        from django.contrib.auth.models import User
        
        # Obtener usuario
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Usuario no encontrado: user_id={user_id}")
            return {'error': 'Usuario no encontrado'}
        
        # Verificar email
        if not user.email:
            logger.warning(f"Usuario sin email: user_id={user_id}")
            return {'error': 'Usuario sin email'}
        
        # Preparar contexto
        if context is None:
            context = {}
        
        context['user'] = user
        context['site_name'] = settings.SITE_NAME if hasattr(settings, 'SITE_NAME') else 'DevBlog'
        context['site_url'] = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'
        
        # Renderizar email
        html_message = render_to_string(template, context)
        plain_message = strip_tags(html_message)
        
        # Enviar email
        from_email = from_email or settings.DEFAULT_FROM_EMAIL
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email enviado: user_id={user_id}, subject={subject}")
        return {'success': True, 'user_id': user_id, 'subject': subject}
    except Exception as e:
        logger.error(f"Error al enviar email: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='accounts.tasks.send_bulk_notifications',
    bind=True,
    max_retries=2,
    queue='notifications',
)
def send_bulk_notifications(self, user_ids, message, link, sender_id=None):
    """
    Crea notificaciones en masa para múltiples usuarios.
    
    Args:
        user_ids: Lista de IDs de usuarios
        message: Mensaje de la notificación
        link: Enlace de la notificación
        sender_id: ID del usuario remitente (opcional)
    """
    try:
        from django.contrib.auth.models import User
        
        # Obtener remitente (admin por defecto)
        if sender_id:
            try:
                sender = User.objects.get(id=sender_id)
            except User.DoesNotExist:
                sender = User.objects.filter(is_superuser=True).first()
        else:
            sender = User.objects.filter(is_superuser=True).first()
        
        # Crear notificaciones en lotes
        batch_size = 100
        total_created = 0
        
        # Procesar en lotes para evitar problemas de memoria
        for i in range(0, len(user_ids), batch_size):
            batch = user_ids[i:i+batch_size]
            
            # Obtener usuarios existentes
            users = User.objects.filter(id__in=batch)
            
            # Crear notificaciones
            notifications = [
                Notification(
                    recipient=user,
                    sender=sender,
                    message=message,
                    link=link,
                    is_read=False
                )
                for user in users
            ]
            
            # Guardar en base de datos
            if notifications:
                Notification.objects.bulk_create(notifications)
                total_created += len(notifications)
        
        logger.info(f"Notificaciones masivas enviadas: {total_created} de {len(user_ids)} usuarios")
        return {'success': True, 'total_created': total_created, 'total_users': len(user_ids)}
    except Exception as e:
        logger.error(f"Error al enviar notificaciones masivas: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='accounts.tasks.cleanup_old_notifications',
    bind=True,
)
def cleanup_old_notifications(self, days=30):
    """
    Elimina notificaciones antiguas que ya han sido leídas.
    
    Args:
        days: Días de antigüedad para eliminar
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Eliminar notificaciones antiguas leídas
        deleted, _ = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()
        
        logger.info(f"Notificaciones antiguas eliminadas: {deleted}")
        return {'success': True, 'deleted': deleted, 'days': days}
    except Exception as e:
        logger.error(f"Error al limpiar notificaciones: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='accounts.tasks.process_user_avatar',
    bind=True,
    queue='media_processing',
)
def process_user_avatar(self, user_id):
    """
    Procesa y optimiza el avatar de un usuario.
    
    Args:
        user_id: ID del usuario
    """
    try:
        from django.contrib.auth.models import User
        from PIL import Image, ImageOps
        from io import BytesIO
        from django.core.files.base import ContentFile
        
        # Obtener usuario y perfil
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
        except (User.DoesNotExist, Profile.DoesNotExist):
            logger.error(f"Usuario o perfil no encontrado: user_id={user_id}")
            return {'error': 'Usuario o perfil no encontrado'}
        
        # Verificar si hay avatar
        if not profile.avatar:
            logger.warning(f"Usuario sin avatar: user_id={user_id}")
            return {'error': 'Usuario sin avatar'}
        
        # Abrir imagen
        with profile.avatar.open('rb') as f:
            img = Image.open(f)
            
            # Convertir modo si es necesario
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Crear versión cuadrada
            square_size = min(img.width, img.height)
            img = ImageOps.fit(img, (square_size, square_size), Image.LANCZOS)
            
            # Crear versiones de diferentes tamaños
            sizes = [
                (150, 150),  # Tamaño normal
                (50, 50),    # Tamaño pequeño
            ]
            
            # Guardar versión original optimizada
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85, optimize=True)
            buffer.seek(0)
            
            # Actualizar avatar
            profile.avatar.save(
                name=profile.avatar.name,
                content=ContentFile(buffer.read()),
                save=True
            )
            
            logger.info(f"Avatar procesado: user_id={user_id}")
            return {'success': True, 'user_id': user_id}
    except Exception as e:
        logger.error(f"Error al procesar avatar: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='accounts.tasks.update_user_stats',
    bind=True,
)
def update_user_stats(self, user_id):
    """
    Actualiza estadísticas de un usuario.
    
    Args:
        user_id: ID del usuario
    """
    try:
        from django.contrib.auth.models import User
        from django.db.models import Count
        
        # Obtener usuario
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Usuario no encontrado: user_id={user_id}")
            return {'error': 'Usuario no encontrado'}
        
        # Calcular estadísticas
        posts_count = user.posts.filter(status='published').count()
        comments_count = user.comments_by_author.filter(active=True).count()
        likes_received = sum(post.likes.count() for post in user.posts.all())
        
        # Actualizar perfil con estadísticas
        # (Aquí se podrían guardar en campos específicos si se añaden al modelo)
        
        logger.info(f"Estadísticas actualizadas: user_id={user_id}")
        return {
            'success': True,
            'user_id': user_id,
            'stats': {
                'posts_count': posts_count,
                'comments_count': comments_count,
                'likes_received': likes_received,
            }
        }
    except Exception as e:
        logger.error(f"Error al actualizar estadísticas: {str(e)}", exc_info=True)
        self.retry(exc=e)