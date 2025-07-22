"""
Utilidades para manejo de caché con Redis.
Proporciona funciones para invalidación, calentamiento y gestión de caché.
"""

import logging
import json
import hashlib
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger('django.cache')

# Configuración de tiempos de caché
CACHE_TIMEOUTS = {
    'posts_list': 300,      # 5 minutos
    'post_detail': 600,     # 10 minutos
    'user_profile': 900,    # 15 minutos
    'search_results': 180,  # 3 minutos
    'tags_list': 1800,      # 30 minutos
    'popular_posts': 600,   # 10 minutos
    'recent_posts': 300,    # 5 minutos
}

def make_cache_key(*args, **kwargs):
    """
    Genera una clave de caché única basada en los argumentos proporcionados.
    
    Args:
        *args: Argumentos posicionales
        **kwargs: Argumentos con nombre
    
    Returns:
        str: Clave de caché única
    """
    # Crear una cadena única con todos los argumentos
    key_parts = []
    
    # Agregar argumentos posicionales
    for arg in args:
        if hasattr(arg, 'id'):
            key_parts.append(f"{arg.__class__.__name__}:{arg.id}")
        else:
            key_parts.append(str(arg))
    
    # Agregar argumentos con nombre
    for key, value in sorted(kwargs.items()):
        key_parts.append(f"{key}:{value}")
    
    # Crear hash MD5 de la clave para evitar claves muy largas
    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"devblog:{key_hash}"

def cache_page_data(cache_key, data, timeout=None):
    """
    Almacena datos en caché con compresión JSON.
    
    Args:
        cache_key: Clave de caché
        data: Datos a almacenar
        timeout: Tiempo de expiración en segundos
    """
    if timeout is None:
        timeout = CACHE_TIMEOUTS.get('default', 300)
    
    try:
        # Serializar datos a JSON para compresión
        if hasattr(data, '__dict__'):
            # Para objetos Django, usar serialización personalizada
            serialized_data = serialize_django_object(data)
        else:
            serialized_data = data
        
        cache.set(cache_key, serialized_data, timeout)
        logger.debug(f"Datos almacenados en caché: {cache_key}")
        
    except Exception as e:
        logger.error(f"Error al almacenar en caché {cache_key}: {e}")

def get_cached_data(cache_key):
    """
    Obtiene datos del caché.
    
    Args:
        cache_key: Clave de caché
    
    Returns:
        Datos del caché o None si no existe
    """
    try:
        data = cache.get(cache_key)
        if data is not None:
            logger.debug(f"Datos obtenidos del caché: {cache_key}")
        return data
    except Exception as e:
        logger.error(f"Error al obtener del caché {cache_key}: {e}")
        return None

def invalidate_cache_pattern(pattern):
    """
    Invalida todas las claves de caché que coincidan con un patrón.
    
    Args:
        pattern: Patrón de clave de caché (ej: "posts:*")
    """
    try:
        # Para Redis, usar el comando KEYS (cuidado en producción)
        if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
            client = cache._cache.get_client()
            keys = client.keys(f"*{pattern}*")
            if keys:
                client.delete(*keys)
                logger.info(f"Invalidadas {len(keys)} claves de caché con patrón: {pattern}")
        else:
            # Fallback para otros backends de caché
            logger.warning(f"No se puede invalidar patrón {pattern} - backend no soportado")
            
    except Exception as e:
        logger.error(f"Error al invalidar patrón de caché {pattern}: {e}")

def warm_cache_for_posts():
    """
    Precalienta el caché con los posts más populares y recientes.
    """
    try:
        from posts.models import Post
        
        # Calentar caché de posts populares
        popular_posts = Post.objects.filter(status='published').order_by('-views')[:10]
        cache_key = make_cache_key('popular_posts')
        cache_page_data(cache_key, list(popular_posts.values()), CACHE_TIMEOUTS['popular_posts'])
        
        # Calentar caché de posts recientes
        recent_posts = Post.objects.filter(status='published').order_by('-created_at')[:10]
        cache_key = make_cache_key('recent_posts')
        cache_page_data(cache_key, list(recent_posts.values()), CACHE_TIMEOUTS['recent_posts'])
        
        logger.info("Caché precalentado para posts populares y recientes")
        
    except Exception as e:
        logger.error(f"Error al precalentar caché de posts: {e}")

def warm_cache_for_tags():
    """
    Precalienta el caché con los tags más utilizados.
    """
    try:
        from taggit.models import Tag
        from django.db.models import Count
        
        # Calentar caché de tags populares
        popular_tags = Tag.objects.annotate(
            post_count=Count('taggit_taggeditem_items')
        ).order_by('-post_count')[:20]
        
        cache_key = make_cache_key('popular_tags')
        cache_page_data(cache_key, list(popular_tags.values()), CACHE_TIMEOUTS['tags_list'])
        
        logger.info("Caché precalentado para tags populares")
        
    except Exception as e:
        logger.error(f"Error al precalentar caché de tags: {e}")

def serialize_django_object(obj):
    """
    Serializa un objeto Django para almacenamiento en caché.
    
    Args:
        obj: Objeto Django a serializar
    
    Returns:
        dict: Datos serializados
    """
    if hasattr(obj, '_meta'):
        # Es un modelo Django
        data = {}
        for field in obj._meta.fields:
            value = getattr(obj, field.name)
            if hasattr(value, 'isoformat'):
                # Convertir fechas a string
                data[field.name] = value.isoformat()
            else:
                data[field.name] = value
        return data
    else:
        return obj

def cache_user_data(user, timeout=900):
    """
    Almacena datos del usuario en caché.
    
    Args:
        user: Usuario de Django
        timeout: Tiempo de expiración en segundos (default: 15 minutos)
    """
    try:
        cache_key = make_cache_key('user_data', user.id)
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined.isoformat(),
        }
        
        # Agregar datos del perfil si existe
        if hasattr(user, 'profile'):
            user_data['profile'] = {
                'bio': user.profile.bio,
                'can_post': user.profile.can_post,
                'permission_requested': user.profile.permission_requested,
            }
        
        cache_page_data(cache_key, user_data, timeout)
        logger.debug(f"Datos de usuario almacenados en caché: {user.username}")
        
    except Exception as e:
        logger.error(f"Error al almacenar datos de usuario en caché: {e}")

def get_cached_user_data(user_id):
    """
    Obtiene datos del usuario del caché.
    
    Args:
        user_id: ID del usuario
    
    Returns:
        dict: Datos del usuario o None
    """
    cache_key = make_cache_key('user_data', user_id)
    return get_cached_data(cache_key)

def invalidate_user_cache(user_id):
    """
    Invalida el caché de un usuario específico.
    
    Args:
        user_id: ID del usuario
    """
    cache_key = make_cache_key('user_data', user_id)
    cache.delete(cache_key)
    logger.debug(f"Caché de usuario invalidado: {user_id}")

def invalidate_post_cache(post_id):
    """
    Invalida el caché relacionado con un post específico.
    
    Args:
        post_id: ID del post
    """
    # Invalidar caché del post específico
    cache_key = make_cache_key('post_detail', post_id)
    cache.delete(cache_key)
    
    # Invalidar listas que podrían contener este post
    invalidate_cache_pattern('posts_list')
    invalidate_cache_pattern('popular_posts')
    invalidate_cache_pattern('recent_posts')
    
    logger.debug(f"Caché de post invalidado: {post_id}")

def get_cache_stats():
    """
    Obtiene estadísticas del caché.
    
    Returns:
        dict: Estadísticas del caché
    """
    try:
        if hasattr(cache, '_cache') and hasattr(cache._cache, 'get_client'):
            client = cache._cache.get_client()
            info = client.info()
            
            return {
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses'),
                'hit_rate': info.get('keyspace_hits', 0) / max(1, info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0)) * 100
            }
        else:
            return {'backend': 'local_memory', 'status': 'active'}
            
    except Exception as e:
        logger.error(f"Error al obtener estadísticas de caché: {e}")
        return {'error': str(e)}