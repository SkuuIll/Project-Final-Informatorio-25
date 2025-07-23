import os
import re
import uuid
import logging
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import AIModel

logger = logging.getLogger(__name__)

def setup_api():
    """
    Configura la API de Google Gemini usando la clave del entorno.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("La variable de entorno GOOGLE_API_KEY no está configurada.")
    genai.configure(api_key=api_key)

def get_active_model_name():
    """
    Obtiene el nombre del modelo de IA activo desde la base de datos.
    """
    try:
        active_model = AIModel.objects.get(is_active=True)
        return active_model.name
    except AIModel.DoesNotExist:
        return 'gemini-2.0-flash-exp'  # Modelo por defecto

def extract_links_from_content(content: str, base_url: str) -> list[str]:
    """
    Extrae todos los enlaces encontrados en el contenido.
    """
    # Buscar URLs en el texto
    url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
    urls = re.findall(url_pattern, content)
    
    # Convertir URLs relativas a absolutas
    absolute_urls = []
    for url in urls:
        if url.startswith('www.'):
            url = 'https://' + url
        elif not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        absolute_urls.append(url)
    
    return list(set(absolute_urls))  # Eliminar duplicados

def extract_images_from_url(url: str, max_images: int = 5) -> list[dict]:
    """
    Extrae imágenes de una URL de manera inteligente, priorizando imágenes de contenido.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        images = []
        
        # Priorizar imágenes dentro del contenido principal
        content_selectors = [
            'article img',
            'main img', 
            '.content img',
            '.post-content img',
            '.entry-content img',
            '[role="main"] img'
        ]
        
        # Buscar imágenes en el contenido principal primero
        for selector in content_selectors:
            content_images = soup.select(selector)
            if content_images:
                for img in content_images[:max_images]:
                    if _is_valid_content_image(img, url):
                        image_data = _process_image_tag(img, url)
                        if image_data and image_data not in images:
                            images.append(image_data)
                            if len(images) >= max_images:
                                return images
                break
        
        # Si no encontramos suficientes imágenes en el contenido, buscar en toda la página
        if len(images) < max_images:
            all_images = soup.find_all('img')
            for img in all_images:
                if len(images) >= max_images:
                    break
                    
                if _is_valid_content_image(img, url):
                    image_data = _process_image_tag(img, url)
                    if image_data and image_data not in images:
                        images.append(image_data)
        
        return images
    
    except requests.RequestException as e:
        print(f"Error al extraer imágenes: {e}")
        return []


def _is_valid_content_image(img_tag, base_url: str) -> bool:
    """
    Determina si una imagen es válida para incluir en el contenido.
    """
    src = img_tag.get('src', '')
    alt = img_tag.get('alt', '')
    
    # Filtrar imágenes no válidas
    invalid_patterns = [
        'logo', 'avatar', 'profile', 'icon', 'button', 'banner', 
        'ad', 'advertisement', 'social', 'share', 'comment',
        'pixel', 'tracking', 'analytics', 'spacer', 'blank'
    ]
    
    # Verificar src
    if not src or any(pattern in src.lower() for pattern in invalid_patterns):
        return False
    
    # Verificar alt text
    if any(pattern in alt.lower() for pattern in invalid_patterns):
        return False
    
    # Verificar extensiones de imagen válidas
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    if not any(ext in src.lower() for ext in valid_extensions):
        return False
    
    # Verificar que no sea una imagen muy pequeña (probablemente decorativa)
    width = img_tag.get('width')
    height = img_tag.get('height')
    
    if width and height:
        try:
            w, h = int(width), int(height)
            if w < 300 or h < 300:  # Filtrar imágenes pequeñas
                return False
        except ValueError:
            pass
    
    # Verificar clases CSS que indican imágenes decorativas
    css_classes = img_tag.get('class', [])
    if isinstance(css_classes, list):
        css_classes = ' '.join(css_classes)
    
    decorative_classes = ['icon', 'logo', 'avatar', 'thumbnail-small', 'decoration']
    if any(cls in css_classes.lower() for cls in decorative_classes):
        return False
    
    return True


def _process_image_tag(img_tag, base_url: str) -> dict:
    """
    Procesa un tag de imagen y devuelve información estructurada.
    """
    src = img_tag.get('src', '')
    if not src:
        return None
    
    # Convertir URL relativa a absoluta
    if not src.startswith(('http://', 'https://')):
        src = urljoin(base_url, src)
    
    # Obtener información adicional
    alt = img_tag.get('alt', '').strip()
    title = img_tag.get('title', '').strip()
    
    # Generar descripción si no hay alt text
    if not alt and not title:
        # Intentar extraer descripción del contexto
        parent = img_tag.parent
        if parent:
            figcaption = parent.find('figcaption')
            if figcaption:
                alt = figcaption.get_text().strip()
    
    return {
        'src': src,
        'alt': alt or 'Imagen del artículo',
        'title': title or alt or 'Imagen relacionada con el contenido',
        'width': img_tag.get('width'),
        'height': img_tag.get('height')
    }


def download_image(image_url: str, folder: str = 'ai_posts/images/', min_width: int = 300, min_height: int = 300) -> str:
    """
    Descarga una imagen y la guarda en el almacenamiento de Django.
    Solo descarga imágenes que cumplan con los requisitos mínimos de tamaño.
    Retorna la URL de la imagen guardada.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Verificar el tamaño de la imagen antes de guardarla
        try:
            from PIL import Image
            import io
            
            # Crear objeto Image desde el contenido descargado
            image_content = io.BytesIO(response.content)
            with Image.open(image_content) as img:
                width, height = img.size
                
                # Verificar que la imagen cumple con los requisitos mínimos
                if width < min_width or height < min_height:
                    print(f"Imagen descartada por tamaño insuficiente: {width}x{height} (mínimo: {min_width}x{min_height}) - {image_url}")
                    return None
                
                print(f"Imagen válida encontrada: {width}x{height} - {image_url}")
                
        except Exception as e:
            print(f"Error al verificar dimensiones de imagen {image_url}: {e}")
            # Si no podemos verificar las dimensiones, continuamos con la descarga
            pass

        # Crear carpeta si no existe
        if not default_storage.exists(folder):
            try:
                os.makedirs(default_storage.path(folder))
                print(f"Carpeta creada: {folder}")
            except Exception as e:
                print(f"Error al crear carpeta {folder}: {e}")

        # Obtener la extensión del archivo
        parsed_url = urlparse(image_url)
        file_extension = os.path.splitext(parsed_url.path)[1]
        if not file_extension:
            file_extension = '.jpg'  # Por defecto

        # Generar nombre único para el archivo
        filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(folder, filename)

        # Guardar el archivo
        file_content = ContentFile(response.content)
        saved_path = default_storage.save(file_path, file_content)
        print(f"Imagen guardada en: {saved_path}")

        return default_storage.url(saved_path)

    except Exception as e:
        print(f"Error al descargar imagen {image_url}: {e}")
        return None

def extract_content_from_url(url: str) -> dict:
    """
    Extrae el contenido, enlaces e imágenes de una URL.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer contenido principal
        article = soup.find('article')
        if not article:
            article = soup.find('main')
        
        if article:
            content = article.get_text(separator='\n', strip=True)
        else:
            content = soup.body.get_text(separator='\n', strip=True)
        
        # Extraer enlaces del contenido
        links = extract_links_from_content(content, url)
        
        return {
            'content': content,
            'links': links,
            'base_url': url
        }
            
    except requests.RequestException as e:
        print(f"Error al descargar la URL: {e}")
        return {
            'content': None,
            'links': [],
            'base_url': url
        }

# Función compatible con el código existente (devuelve tupla)
def rewrite_content_with_ai(content: str, prompt_template: str, urls: list = None) -> tuple[str, str]:
    """
    Usa Gemini para reescribir el contenido y generar un título.
    Versión compatible que devuelve tupla (título, contenido).
    """
    result = rewrite_content_with_ai_advanced(content, prompt_template, urls)
    return result['title'], result['content']

def rewrite_content_with_ai_advanced(content: str, prompt_template: str, urls: list = None) -> dict:
    """
    Usa Gemini para reescribir el contenido, generar título y extraer tags.
    Versión avanzada que devuelve diccionario completo.
    """
    setup_api()
    model_name = get_active_model_name()
    model = genai.GenerativeModel(model_name)
    
    # Preparar el prompt con URLs si están disponibles
    urls_text = "\n".join(urls) if urls else "No se encontraron URLs adicionales"
    prompt = prompt_template.format(content=content, urls=urls_text)
    
    response = model.generate_content(prompt)
    
    try:
        # Dividir la respuesta en secciones
        response_text = response.text
        
        # Buscar tags si están incluidos
        if "---TAGS---" in response_text:
            parts = response_text.split("---TAGS---")
            main_content = parts[0].strip()
            tags_text = parts[1].strip() if len(parts) > 1 else ""
            tags = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        else:
            main_content = response_text
            tags = []
        
        # Separar título y contenido
        if '---' in main_content:
            content_parts = main_content.split('---', 1)
            title = content_parts[0].strip()
            body = content_parts[1].strip()
        else:
            title = "Título no generado"
            body = main_content
        
        return {
            'title': title,
            'content': body,
            'tags': tags,
            'raw_response': response_text
        }
    
    except (IndexError, AttributeError) as e:
        print(f"Error al procesar respuesta de AI: {e}")
        return {
            'title': "Título no generado",
            'content': response.text if hasattr(response, 'text') else "Contenido no generado",
            'tags': [],
            'raw_response': response.text if hasattr(response, 'text') else ""
        }

def generate_tags_with_ai(content: str, prompt_template: str) -> list[str]:
    """
    Usa Gemini para generar una lista de tags a partir del contenido.
    """
    setup_api()
    model_name = get_active_model_name()
    model = genai.GenerativeModel(model_name)
    prompt = prompt_template.format(content=content)
    
    response = model.generate_content(prompt)
    
    try:
        tags = [tag.strip() for tag in response.text.split(',')]
        return tags
    except AttributeError:
        return []

def process_images_in_content(content: str, images_data: list[dict]) -> str:
    """
    Procesa el contenido HTML y reemplaza los comentarios de imágenes sugeridas
    con imágenes reales si están disponibles.
    """
    if not images_data:
        return content
    
    # Buscar comentarios de imágenes sugeridas
    image_comment_pattern = r'<!-- IMAGEN SUGERIDA: ([^>]+) -->'
    
    used_images = set()
    image_index = 0
    
    def replace_image_comment(match):
        nonlocal image_index
        description = match.group(1)
        
        # Insertar la siguiente imagen no usada
        while image_index < len(images_data):
            img_data = images_data[image_index]
            image_index += 1
            local_url = img_data.get('local_url')
            if local_url and local_url not in used_images:
                used_images.add(local_url)
                return f'<p><img src="{local_url}" alt="{img_data.get("alt", description)}" style="max-width: 100%; height: auto;"></p>'
        
        # Si no hay imagen disponible, mantener el comentario
        return match.group(0)
    
    return re.sub(image_comment_pattern, replace_image_comment, content)

def generate_complete_post(
    url: str, 
    rewrite_prompt: str,  
    extract_images: bool = True, 
    max_images: int = 5,
    title: str = None,
    generate_cover: bool = True,
    image_style: str = 'professional',
    progress_callback: callable = None
) -> dict:
    """
    Genera un post completo a partir de una URL.
    
    Args:
        url: URL del artículo a procesar
        rewrite_prompt: Instrucciones para reescribir el contenido
        extract_images: Si se deben extraer imágenes
        max_images: Número máximo de imágenes a extraer
        title: Título personalizado (opcional)
        generate_cover: Si se debe generar una imagen de portada
        image_style: Estilo de la imagen de portada
        progress_callback: Función para reportar progreso (opcional)
        
    Returns:
        Diccionario con el resultado del proceso
    """
    def report_progress(step: str, percentage: int):
        """Helper function to report progress"""
        if progress_callback:
            try:
                progress_callback(step, percentage)
            except Exception as e:
                logger.warning(f"Error reporting progress: {e}")
    
    if not url and not title:
        return {
            'success': False,
            'error': 'Se requiere una URL o un título personalizado.'
        }
    
    report_progress("Iniciando generación de post", 0)
    
    # Extraer contenido de la URL si se proporciona
    content = None
    if url:
        report_progress("Extrayendo contenido de URL", 10)
        content_result = extract_content_from_url(url)
        if not content_result['success']:
            return content_result
        content = content_result['content']
        report_progress("Contenido extraído exitosamente", 20)
    
    # Extraer imágenes si está habilitado
    images_data = []
    if extract_images and url:
        report_progress("Extrayendo imágenes", 25)
        images_info = extract_images_from_url(url, max_images)
        for i, img_info in enumerate(images_info):
            local_url = download_image(img_info['src'], min_width=300, min_height=300)
            if local_url:
                img_info['local_url'] = local_url
                images_data.append(img_info)
            # Report progress for image extraction
            progress = 25 + (i + 1) * 10 / len(images_info)
            report_progress(f"Procesando imagen {i + 1}/{len(images_info)}", int(progress))
        report_progress("Imágenes procesadas", 35)
    
    # Reescribir contenido con IA
    report_progress("Generando contenido con IA", 40)
    if content:
        ai_title, ai_content = rewrite_content_with_ai(
            content=content,
            prompt_template=rewrite_prompt
        )
        ai_result = {
            'success': True,
            'title': title if title else ai_title,
            'content': ai_content
        }
    else:
        # Si no hay contenido de URL, usar solo el título proporcionado
        ai_result = {
            'success': True,
            'title': title or 'Post generado con IA',
            'content': 'Contenido generado automáticamente.'
        }
    
    if not ai_result['success']:
        return ai_result
    
    report_progress("Contenido generado exitosamente", 50)
    
    # Generar tags
    report_progress("Generando tags", 55)
    try:
        # Usar un prompt básico para generar tags
        tag_prompt = "Genera 5 tags relevantes para este contenido, separados por comas: {content}"
        ai_result['tags'] = generate_tags_with_ai(ai_result['content'], tag_prompt)
        report_progress("Tags generados", 60)
    except Exception as e:
        logger.warning(f"Error generating tags: {e}")
        ai_result['tags'] = []
        report_progress("Tags no disponibles", 60)
    
    # Calcular tiempo de lectura
    def calculate_reading_time(content):
        """Calcula el tiempo de lectura estimado en minutos"""
        if not content:
            return 0
        # Aproximadamente 200 palabras por minuto
        word_count = len(content.split())
        return max(1, round(word_count / 200))
    
    ai_result['reading_time'] = calculate_reading_time(ai_result['content'])
    
    # Insertar imágenes en el contenido si hay disponibles
    report_progress("Procesando imágenes en contenido", 65)
    final_content = ai_result['content']
    if images_data:
        final_content = process_images_in_content(final_content, images_data)
        report_progress("Imágenes insertadas en contenido", 70)
    
    ai_result['content'] = final_content
    ai_result['images'] = images_data
    
    # Generar imagen de portada si está habilitado
    if generate_cover:
        report_progress("Generando imagen de portada", 75)
        try:
            from posts.image_generation import registry, CoverImagePromptBuilder
            
            logger.info("Starting cover image generation...")
            
            # Obtener el servicio de generación de imágenes
            service = registry.get_default_service()
            if service:
                logger.info(f"Using image service: {service.__class__.__name__}")
                report_progress("Construyendo prompt para imagen", 80)
                
                # Construir prompt optimizado para la imagen
                prompt = CoverImagePromptBuilder.build_cover_prompt(
                    title=ai_result['title'],
                    content=ai_result['content'],
                    tags=ai_result['tags'],
                    style=image_style
                )
                
                logger.info(f"Generated prompt for image: {prompt[:100]}...")
                
                # Generar la imagen con reintentos
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        report_progress(f"Generando imagen (intento {attempt + 1})", 85 + attempt * 3)
                        success, image_url, error = service.generate_image(prompt)
                        
                        if success and image_url:
                            ai_result['cover_image_url'] = image_url
                            logger.info(f"Cover image generated successfully: {image_url}")
                            report_progress("Imagen de portada generada", 95)
                            break
                        else:
                            logger.warning(f"Attempt {attempt + 1} failed to generate cover image: {error}")
                            if attempt == max_retries - 1:
                                logger.error("All attempts to generate cover image failed")
                                report_progress("Error generando imagen de portada", 95)
                    except Exception as e:
                        logger.error(f"Attempt {attempt + 1} error generating cover image: {e}")
                        if attempt == max_retries - 1:
                            logger.error("All attempts to generate cover image failed due to errors")
                            report_progress("Error generando imagen de portada", 95)
            else:
                logger.warning("No image generation service available")
                report_progress("Servicio de imágenes no disponible", 95)
                # Fallback: continue without cover image
                
        except ImportError:
            logger.warning("Image generation modules not available, skipping cover image generation")
            report_progress("Módulos de imagen no disponibles", 95)
        except Exception as e:
            logger.error(f"Unexpected error generating cover image: {e}")
            report_progress("Error inesperado con imagen", 95)
            # Fallback: continue without cover image
    else:
        report_progress("Omitiendo generación de imagen", 95)
    
    report_progress("Post generado exitosamente", 100)
    return ai_result
