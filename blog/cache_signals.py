"""
Señales para invalidación automática de caché.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from posts.models import Post, Comment
from accounts.models import Profile
from blog.cache_utils import (
    invalidate_post_cache,
    invalidate_user_cache,
    invalidate_cache_pattern
)
import logging

logger = logging.getLogger('django.cache')

@receiver(post_save, sender=Post)
def invalidate_post_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalida el caché cuando se guarda un post.
    """
    try:
        # Invalidar caché del post específico
        invalidate_post_cache(instance.id)
        
        # Invalidar listas relacionadas
        invalidate_cache_pattern('posts_list')
        invalidate_cache_pattern('popular_posts')
        invalidate_cache_pattern('recent_posts')
        
        # Si es un post nuevo, invalidar más cachés
        if created:
            invalidate_cache_pattern('user_posts')
            invalidate_user_cache(instance.author.id)
        
        logger.info(f"Caché invalidado para post: {instance.title}")
        
    except Exception as e:
        logger.error(f"Error al invalidar caché de post: {e}")

@receiver(post_delete, sender=Post)
def invalidate_post_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida el caché cuando se elimina un post.
    """
    try:
        # Invalidar caché del post específico
        invalidate_post_cache(instance.id)
        
        # Invalidar listas relacionadas
        invalidate_cache_pattern('posts_list')
        invalidate_cache_pattern('popular_posts')
        invalidate_cache_pattern('recent_posts')
        invalidate_cache_pattern('user_posts')
        
        # Invalidar caché del usuario
        invalidate_user_cache(instance.author.id)
        
        logger.info(f"Caché invalidado para post eliminado: {instance.title}")
        
    except Exception as e:
        logger.error(f"Error al invalidar caché de post eliminado: {e}")

@receiver(post_save, sender=Comment)
def invalidate_comment_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalida el caché cuando se guarda un comentario.
    """
    try:
        # Invalidar caché del post relacionado
        invalidate_post_cache(instance.post.id)
        
        # Invalidar listas de comentarios
        invalidate_cache_pattern('comments')
        
        logger.info(f"Caché invalidado para comentario en post: {instance.post.title}")
        
    except Exception as e:
        logger.error(f"Error al invalidar caché de comentario: {e}")

@receiver(post_delete, sender=Comment)
def invalidate_comment_cache_on_delete(sender, instance, **kwargs):
    """
    Invalida el caché cuando se elimina un comentario.
    """
    try:
        # Invalidar caché del post relacionado
        invalidate_post_cache(instance.post.id)
        
        # Invalidar listas de comentarios
        invalidate_cache_pattern('comments')
        
        logger.info(f"Caché invalidado para comentario eliminado en post: {instance.post.title}")
        
    except Exception as e:
        logger.error(f"Error al invalidar caché de comentario eliminado: {e}")

@receiver(post_save, sender=User)
def invalidate_user_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalida el caché cuando se actualiza un usuario.
    """
    try:
        # Invalidar caché del usuario
        invalidate_user_cache(instance.id)
        
        # Si es un usuario nuevo, invalidar listas de usuarios
        if created:
            invalidate_cache_pattern('users_list')
        
        logger.info(f"Caché invalidado para usuario: {instance.username}")
        
    except Exception as e:
        logger.error(f"Error al invalidar caché de usuario: {e}")

@receiver(post_save, sender=Profile)
def invalidate_profile_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalida el caché cuando se actualiza un perfil.
    """
    try:
        # Invalidar caché del usuario relacionado
        invalidate_user_cache(instance.user.id)
        
        # Invalidar listas de perfiles
        invalidate_cache_pattern('profiles')
        
        logger.info(f"Caché invalidado para perfil de usuario: {instance.user.username}")
        
    except Exception as e:
        logger.error(f"Error al invalidar caché de perfil: {e}")

# Función para conectar todas las señales
def connect_cache_signals():
    """
    Conecta todas las señales de invalidación de caché.
    Esta función debe ser llamada en apps.py o __init__.py
    """
    logger.info("Señales de caché conectadas correctamente")