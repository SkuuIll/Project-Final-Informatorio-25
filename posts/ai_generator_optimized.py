"""
Versión optimizada del generador de IA con manejo de memoria y timeouts.
"""

import logging
import time
from typing import Dict, Optional, Callable
import google.generativeai as genai
from .ai_memory_optimizer import (
    memory_optimized, 
    ProgressTracker, 
    timeout_handler,
    get_ai_config
)

logger = logging.getLogger(__name__)

@memory_optimized
@timeout_handler(timeout_seconds=get_ai_config('timeout_seconds', 240))
def generate_complete_post_optimized(
    url: Optional[str] = None,
    title: Optional[str] = None,
    rewrite_prompt: Optional[str] = None,
    extract_images: bool = True,
    max_images: int = 3,
    progress_callback: Optional[Callable] = None,
    **kwargs
) -> Dict:
    """
    Versión optimizada de generación de posts con IA.
    Incluye manejo de memoria y timeouts mejorados.
    """
    
    # Crear tracker de progreso optimizado
    tracker = ProgressTracker(progress_callback)
    
    try:
        # Configurar API
        from .ai_generator import setup_api
        setup_api()
        
        result = {
            'success': False,
            'title': '',
            'content': '',
            'tags': [],
            'reading_time': 0,
            'extracted_images': [],
            'cover_image': None
        }
        
        # Paso 1: Extraer contenido de URL o usar título
        tracker.update("Iniciando generación...", 10)
        
        if url:
            from .ai_generator import extract_content_from_url
            tracker.update("Extrayendo contenido de URL...", 20)
            
            extraction_result = extract_content_from_url(url)
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': extraction_result['error']
                }
            
            result['title'] = extraction_result.get('title', title or 'Post generado con IA')
            content = extraction_result['content']
        else:
            if not title:
                return {
                    'success': False,
                    'error': 'Se requiere una URL o un título para generar el post'
                }
            
            result['title'] = title
            content = f"Crear contenido sobre: {title}"
        
        # Paso 2: Reescribir contenido (optimizado)
        tracker.update("Reescribiendo contenido con IA...", 40)
        
        rewrite_result = rewrite_content_optimized(content, rewrite_prompt, tracker)
        if not rewrite_result['success']:
            return {
                'success': False,
                'error': rewrite_result['error']
            }
        
        result['content'] = rewrite_result['content']
        
        # Paso 3: Generar tags (optimizado)
        tracker.update("Generando tags...", 70)
        
        tags_result = generate_tags_optimized(result['content'], tracker)
        if tags_result['success']:
            result['tags'] = tags_result['tags']
        else:
            # Tags por defecto si falla
            result['tags'] = ['tecnología', 'blog', 'desarrollo']
        
        # Paso 4: Calcular tiempo de lectura
        from .ai_generator import calculate_reading_time
        result['reading_time'] = calculate_reading_time(result['content'])
        
        # Paso 5: Procesar imágenes si se solicita
        if extract_images and url:
            tracker.update("Procesando imágenes...", 85)
            
            try:
                from .ai_generator import extract_and_process_images
                prioritize_large = kwargs.get('prioritize_large_images', True)
                extracted_images = extract_and_process_images(url, max_images, prioritize_large)
                result['extracted_images'] = extracted_images
                
                # Insertar imágenes en el contenido
                if extracted_images:
                    result['content'] = insert_images_in_content(result['content'], extracted_images)
                
            except Exception as e:
                logger.warning(f"Error procesando imágenes: {e}")
                # Continuar sin imágenes
        
        # Paso 6: Generar imagen de portada si se solicita
        if kwargs.get('generate_cover_image', False):
            tracker.update("Generando imagen de portada...", 95)
            
            try:
                cover_result = generate_cover_image_optimized(result['title'], result['content'])
                if cover_result['success']:
                    result['cover_image'] = cover_result['image_path']
            except Exception as e:
                logger.warning(f"Error generando imagen de portada: {e}")
                # Continuar sin imagen de portada
        
        tracker.update("Finalizando...", 100)
        result['success'] = True
        
        return result
        
    except TimeoutError:
        return {
            'success': False,
            'error': 'La generación del post excedió el tiempo límite. Intenta con contenido más corto.'
        }
    except Exception as e:
        logger.error(f"Error en generación optimizada: {e}")
        return {
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }
    finally:
        tracker.finish()

@memory_optimized
def rewrite_content_optimized(content: str, prompt: Optional[str], tracker: ProgressTracker) -> Dict:
    """Versión optimizada de reescritura de contenido."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        if not prompt:
            prompt = """
            Reescribe el siguiente contenido de manera profesional y atractiva para un blog de tecnología.
            Mantén la información técnica precisa pero hazla más accesible.
            Estructura el contenido con párrafos claros y un flujo lógico.
            Máximo 1500 palabras.
            """
        
        # Limitar el contenido para evitar timeouts
        if len(content) > 5000:
            content = content[:5000] + "..."
            logger.info("Contenido truncado para optimizar procesamiento")
        
        full_prompt = f"{prompt}\n\nContenido a reescribir:\n{content}"
        
        tracker.update("Enviando contenido a IA...", 45)
        response = model.generate_content(full_prompt)
        
        if not response.text:
            return {
                'success': False,
                'error': 'No se recibió respuesta del modelo de IA'
            }
        
        tracker.update("Contenido reescrito exitosamente", 60)
        
        return {
            'success': True,
            'content': response.text.strip()
        }
        
    except Exception as e:
        logger.error(f"Error en reescritura optimizada: {e}")
        return {
            'success': False,
            'error': f'Error en la reescritura: {str(e)}'
        }

@memory_optimized
def generate_tags_optimized(content: str, tracker: ProgressTracker) -> Dict:
    """Versión optimizada de generación de tags."""
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Usar solo los primeros 1000 caracteres para tags
        content_sample = content[:1000] if len(content) > 1000 else content
        
        prompt = f"""
        Analiza el siguiente contenido y genera entre 3 y 6 tags relevantes.
        Los tags deben ser:
        - Específicos y relevantes al contenido
        - En español
        - Una sola palabra o máximo dos palabras
        - Relacionados con tecnología, programación o el tema principal
        
        Devuelve solo los tags separados por comas, sin explicaciones adicionales.
        
        Contenido: {content_sample}
        """
        
        tracker.update("Generando tags con IA...", 75)
        response = model.generate_content(prompt)
        
        if not response.text:
            return {
                'success': False,
                'error': 'No se pudieron generar tags'
            }
        
        # Procesar tags
        tags_text = response.text.strip()
        tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        
        # Limitar a máximo 6 tags
        tags = tags[:6]
        
        tracker.update("Tags generados exitosamente", 80)
        
        return {
            'success': True,
            'tags': tags
        }
        
    except Exception as e:
        logger.error(f"Error generando tags optimizados: {e}")
        return {
            'success': False,
            'error': f'Error generando tags: {str(e)}'
        }

def insert_images_in_content(content: str, images: list) -> str:
    """Inserta imágenes en el contenido de manera optimizada."""
    if not images:
        return content
    
    # Insertar primera imagen después del primer párrafo
    paragraphs = content.split('\n\n')
    if len(paragraphs) > 1 and images:
        first_image = images[0]
        image_html = f'\n\n<img src="{first_image["url"]}" alt="{first_image.get("alt", "Imagen del post")}" style="max-width: 100%; height: auto;">\n\n'
        paragraphs.insert(1, image_html)
    
    return '\n\n'.join(paragraphs)

@memory_optimized
def generate_cover_image_optimized(title: str, content: str) -> Dict:
    """Genera imagen de portada de manera optimizada."""
    try:
        from .ai_generator import generate_image_with_ai
        
        # Crear prompt simple para la imagen
        prompt = f"Imagen profesional para blog sobre: {title}"
        
        result = generate_image_with_ai(prompt)
        return result
        
    except Exception as e:
        logger.error(f"Error generando imagen de portada: {e}")
        return {
            'success': False,
            'error': f'Error generando imagen: {str(e)}'
        }