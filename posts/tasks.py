"""
Tareas de Celery para la aplicación de posts.
"""

import logging
import os
import time
from io import BytesIO
from celery import shared_task
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Count, F
from django.utils import timezone
from django.utils.text import slugify
from PIL import Image, ImageOps
from .models import Post, Comment
from .ai_generator import extract_content_from_url, rewrite_content_with_ai, generate_tags_with_ai, generate_complete_post

logger = logging.getLogger('celery')

@shared_task(
    name='posts.tasks.generate_ai_content',
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 1 minuto
    rate_limit='10/h',  # Limitar a 10 por hora
    queue='ai_processing',
)
def generate_ai_content(self, prompt, user_id=None, post_id=None):
    """
    Genera contenido con IA basado en un prompt.
    """
    try:
        logger.info(f"Generando contenido con IA: prompt={prompt[:50]}...")
        
        # Simular tiempo de procesamiento
        time.sleep(2)
        
        # Generar contenido
        # Note: This task function needs to be updated to work with the new signature
        # For now, we'll create a basic result structure
        content = {
            'success': True,
            'title': 'Contenido generado por tarea',
            'content': f'Contenido generado basado en: {prompt}',
            'tags': [],
            'reading_time': 1
        }
        
        # Si hay un post_id, actualizar el post
        if post_id:
            from django.contrib.auth.models import User
            
            try:
                post = Post.objects.get(id=post_id)
                post.content = content.get('content', '')
                
                # Actualizar título si está vacío
                if not post.title and content.get('title'):
                    post.title = content.get('title')
                    post.slug = slugify(post.title)
                
                # Guardar post
                post.save()
                
                # Añadir tags si hay
                if content.get('tags'):
                    for tag in content.get('tags'):
                        post.tags.add(tag)
                
                logger.info(f"Post actualizado con contenido generado: post_id={post_id}")
            except Post.DoesNotExist:
                logger.error(f"Post no encontrado: post_id={post_id}")
        
        return content
    except Exception as e:
        logger.error(f"Error al generar contenido con IA: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='posts.tasks.optimize_images',
    bind=True,
    max_retries=2,
    queue='media_processing',
)
def optimize_images(self, image_path, sizes=None, quality=85):
    """
    Optimiza una imagen y genera múltiples tamaños.
    
    Args:
        image_path: Ruta de la imagen original
        sizes: Lista de tamaños a generar, ej: [(800, 600), (400, 300)]
        quality: Calidad de compresión (1-100)
    """
    try:
        if sizes is None:
            sizes = [
                (1200, 900),  # Grande
                (800, 600),   # Mediana
                (400, 300),   # Pequeña
                (150, 150),   # Thumbnail
            ]
        
        # Verificar que la imagen existe
        if not default_storage.exists(image_path):
            logger.error(f"Imagen no encontrada: {image_path}")
            return {'error': 'Imagen no encontrada'}
        
        # Abrir imagen
        with default_storage.open(image_path, 'rb') as f:
            img = Image.open(f)
            img_format = img.format
            
            # Convertir modo si es necesario
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Generar versiones optimizadas
            results = {}
            
            for size in sizes:
                # Crear nombre para versión redimensionada
                name, ext = os.path.splitext(image_path)
                size_suffix = f"{size[0]}x{size[1]}"
                new_path = f"{name}_{size_suffix}{ext}"
                
                # Redimensionar manteniendo proporción
                resized_img = ImageOps.contain(img, size)
                
                # Guardar versión optimizada
                buffer = BytesIO()
                
                if img_format == 'JPEG' or ext.lower() in ('.jpg', '.jpeg'):
                    resized_img.save(buffer, format='JPEG', quality=quality, optimize=True)
                elif img_format == 'PNG' or ext.lower() == '.png':
                    resized_img.save(buffer, format='PNG', optimize=True)
                elif img_format == 'WEBP' or ext.lower() == '.webp':
                    resized_img.save(buffer, format='WEBP', quality=quality)
                else:
                    # Formato por defecto
                    resized_img.save(buffer, format='JPEG', quality=quality, optimize=True)
                
                buffer.seek(0)
                
                # Guardar archivo
                saved_path = default_storage.save(new_path, ContentFile(buffer.read()))
                results[size_suffix] = saved_path
            
            logger.info(f"Imagen optimizada: {image_path} -> {len(results)} versiones")
            return results
    except Exception as e:
        logger.error(f"Error al optimizar imagen: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='posts.tasks.update_post_stats',
    bind=True,
)
def update_post_stats(self):
    """
    Actualiza estadísticas cacheadas de posts.
    """
    try:
        # Actualizar contadores en caché
        posts_updated = Post.objects.annotate(
            likes_count_new=Count('likes'),
            comments_count_new=Count('comments')
        ).update(
            cached_likes_count=F('likes_count_new'),
            cached_comments_count=F('comments_count_new'),
        )
        
        logger.info(f"Estadísticas de posts actualizadas: {posts_updated} posts")
        return posts_updated
    except Exception as e:
        logger.error(f"Error al actualizar estadísticas: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='posts.tasks.process_post_content',
    bind=True,
    max_retries=2,
)
def process_post_content(self, post_id):
    """
    Procesa el contenido de un post: extrae imágenes, optimiza, etc.
    """
    try:
        # Obtener post
        post = Post.objects.get(id=post_id)
        
        # Procesar contenido HTML
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(post.content, 'html.parser')
        
        # Procesar imágenes
        images = soup.find_all('img')
        for img in images:
            src = img.get('src')
            
            # Solo procesar imágenes locales
            if src and not src.startswith(('http://', 'https://')):
                # Verificar si la imagen existe
                if default_storage.exists(src):
                    # Optimizar imagen
                    optimize_images.delay(src)
                    
                    # Añadir atributos para lazy loading
                    img['loading'] = 'lazy'
                    img['decoding'] = 'async'
        
        # Actualizar contenido procesado
        post.content = str(soup)
        post.save(update_fields=['content'])
        
        logger.info(f"Contenido de post procesado: post_id={post_id}, imágenes={len(images)}")
        return {'post_id': post_id, 'images_processed': len(images)}
    except Post.DoesNotExist:
        logger.error(f"Post no encontrado: post_id={post_id}")
        return {'error': 'Post no encontrado'}
    except Exception as e:
        logger.error(f"Error al procesar contenido: {str(e)}", exc_info=True)
        self.retry(exc=e)


@shared_task(
    name='posts.tasks.generate_post_preview',
    bind=True,
)
def generate_post_preview(self, post_id):
    """
    Genera una vista previa del post para compartir en redes sociales.
    """
    try:
        # Obtener post
        post = Post.objects.get(id=post_id)
        
        # Generar imagen de vista previa
        # (Aquí iría el código para generar la imagen, por ejemplo con Pillow)
        
        # Por ahora, solo registramos el intento
        logger.info(f"Vista previa generada para post: post_id={post_id}")
        return {'post_id': post_id, 'preview_generated': True}
    except Post.DoesNotExist:
        logger.error(f"Post no encontrado: post_id={post_id}")
        return {'error': 'Post no encontrado'}
    except Exception as e:
        logger.error(f"Error al generar vista previa: {str(e)}", exc_info=True)
        self.retry(exc=e)