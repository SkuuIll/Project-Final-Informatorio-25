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
        return os.getenv('GEMINI_TEXT_MODEL', 'gemini-2.5-pro')  # Usar Gemini 2.5-pro por defecto

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
    
    return absolute_urls

def extract_content_from_url(url: str) -> dict:
    """
    Extrae el contenido principal de una URL.
    
    Returns:
        dict: Diccionario con 'success', 'title', 'content', 'error'
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer título
        title = ""
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Extraer contenido principal
        content = ""
        
        # Buscar contenido en diferentes elementos comunes
        content_selectors = [
            'article',
            '.content',
            '.post-content',
            '.entry-content',
            '.article-content',
            'main',
            '.main-content'
        ]
        
        for selector in content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                content = content_element.get_text(separator=' ', strip=True)
                break
        
        # Si no se encuentra contenido específico, usar el body
        if not content:
            body = soup.find('body')
            if body:
                # Remover scripts y estilos
                for script in body(["script", "style"]):
                    script.decompose()
                content = body.get_text(separator=' ', strip=True)
        
        # Limpiar contenido
        content = re.sub(r'\s+', ' ', content).strip()
        
        if not content:
            return {
                'success': False,
                'error': 'No se pudo extraer contenido de la URL'
            }
        
        return {
            'success': True,
            'title': title,
            'content': content[:5000],  # Limitar a 5000 caracteres
            'url': url
        }
        
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Error al acceder a la URL: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error procesando contenido: {str(e)}'
        }

def rewrite_content_with_ai(content: str, prompt: str = None, progress_callback=None) -> dict:
    """
    Reescribe el contenido usando IA.
    
    Returns:
        dict: Diccionario con 'success', 'content', 'error'
    """
    try:
        setup_api()
        # Usar Gemini 2.5-pro para mejor calidad de contenido
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        if progress_callback:
            progress_callback("Reescribiendo contenido con IA...", 30)
        
        # Prompt por defecto si no se proporciona uno
        if not prompt:
            prompt = """
            Reescribe el siguiente contenido de manera profesional y atractiva para un blog de tecnología.
            Mantén la información técnica precisa pero hazla más accesible.
            Estructura el contenido con párrafos claros y un flujo lógico.
            """
        
        full_prompt = f"{prompt}\n\nContenido a reescribir:\n{content}"
        
        response = model.generate_content(full_prompt)
        
        if not response.text:
            return {
                'success': False,
                'error': 'No se recibió respuesta del modelo de IA'
            }
        
        return {
            'success': True,
            'content': response.text.strip()
        }
        
    except Exception as e:
        logger.error(f"Error reescribiendo contenido: {e}")
        return {
            'success': False,
            'error': f'Error en la reescritura: {str(e)}'
        }

def generate_tags_with_ai(content: str, progress_callback=None) -> dict:
    """
    Genera tags usando IA basándose en el contenido.
    
    Returns:
        dict: Diccionario con 'success', 'tags', 'error'
    """
    try:
        setup_api()
        # Usar Gemini 2.5-pro para mejor calidad de tags
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        if progress_callback:
            progress_callback("Generando tags con IA...", 70)
        
        prompt = f"""
        Analiza el siguiente contenido y genera entre 3 y 6 tags relevantes.
        Los tags deben ser:
        - Específicos y relevantes al contenido
        - En español
        - Una sola palabra o máximo dos palabras
        - Relacionados con tecnología, programación o el tema principal
        
        Devuelve solo los tags separados por comas, sin explicaciones adicionales.
        
        Contenido:
        {content[:2000]}
        """
        
        response = model.generate_content(prompt)
        
        if not response.text:
            return {
                'success': False,
                'error': 'No se pudieron generar tags'
            }
        
        # Procesar tags
        tags_text = response.text.strip()
        tags = [tag.strip() for tag in tags_text.split(',')]
        tags = [tag for tag in tags if tag and len(tag) > 1][:6]  # Máximo 6 tags
        
        return {
            'success': True,
            'tags': tags
        }
        
    except Exception as e:
        logger.error(f"Error generando tags: {e}")
        return {
            'success': False,
            'error': f'Error generando tags: {str(e)}'
        }

def calculate_reading_time(content: str) -> int:
    """
    Calcula el tiempo de lectura estimado en minutos.
    """
    if not content:
        return 1
    
    # Contar palabras
    words = len(content.split())
    
    # Promedio de 200 palabras por minuto
    reading_time = max(1, round(words / 200))
    
    return reading_time

def extract_and_process_images(url: str, max_images: int = 5, prioritize_large: bool = True) -> list:
    """
    Extrae imágenes de una URL y las procesa para uso en el post.
    
    Args:
        url (str): URL de donde extraer las imágenes
        max_images (int): Número máximo de imágenes a extraer
        
    Returns:
        list: Lista de diccionarios con información de las imágenes procesadas
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        
        # Encontrar todas las imágenes
        img_tags = soup.find_all('img')
        
        # Filtrar y priorizar imágenes si se solicita
        if prioritize_large:
            # Filtrar imágenes que probablemente sean de contenido (no iconos/logos pequeños)
            filtered_imgs = []
            for img in img_tags:
                # Obtener dimensiones si están disponibles
                width = img.get('width')
                height = img.get('height')
                
                # Filtrar por tamaño si está disponible
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if w >= 400 and h >= 400:  # Mínimo 400x400 píxeles
                            filtered_imgs.append(img)
                    except ValueError:
                        # Si no se puede parsear, verificar después de descargar
                        filtered_imgs.append(img)
                else:
                    # Si no hay dimensiones, verificar después de descargar
                    filtered_imgs.append(img)
            
            # Si después del filtrado no hay suficientes, usar todas
            if len(filtered_imgs) < max_images // 2:
                img_tags = img_tags[:max_images]
            else:
                img_tags = filtered_imgs[:max_images]
        else:
            img_tags = img_tags[:max_images]
        
        processed_images = []
        
        for i, img in enumerate(img_tags):
            try:
                # Obtener URL de la imagen
                img_src = img.get('src')
                if not img_src:
                    continue
                
                # Convertir URL relativa a absoluta
                if img_src.startswith('//'):
                    img_url = f"https:{img_src}"
                elif img_src.startswith('/'):
                    img_url = f"{base_url}{img_src}"
                elif not img_src.startswith(('http://', 'https://')):
                    img_url = urljoin(url, img_src)
                else:
                    img_url = img_src
                
                # Obtener información adicional
                alt_text = img.get('alt', '')
                title_text = img.get('title', '')
                
                # Descargar y guardar la imagen
                try:
                    img_response = requests.get(img_url, headers=headers, timeout=15)
                    img_response.raise_for_status()
                    
                    # Verificar que es una imagen válida
                    content_type = img_response.headers.get('content-type', '')
                    if not content_type.startswith('image/'):
                        continue
                    
                    # Generar nombre único
                    file_extension = img_url.split('.')[-1].split('?')[0][:4]  # Limitar extensión
                    if file_extension.lower() not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                        file_extension = 'jpg'
                    
                    filename = f"extracted_{uuid.uuid4().hex[:8]}.{file_extension}"
                    file_path = f"ai_posts/content/{filename}"
                    
                    # Verificar dimensiones de la imagen descargada
                    from PIL import Image as PILImage
                    from io import BytesIO
                    
                    try:
                        # Abrir imagen para verificar dimensiones
                        img_buffer = BytesIO(img_response.content)
                        with PILImage.open(img_buffer) as pil_img:
                            img_width, img_height = pil_img.size
                            
                            # Verificar que cumple con el tamaño mínimo de 400x400
                            if img_width < 400 or img_height < 400:
                                logger.info(f"Imagen descartada por tamaño pequeño: {img_width}x{img_height} (mínimo 400x400)")
                                continue
                                
                            logger.info(f"Imagen válida: {img_width}x{img_height}")
                    except Exception as e:
                        logger.warning(f"Error verificando dimensiones de imagen: {e}")
                        continue
                    
                    # Guardar imagen
                    from django.core.files.base import ContentFile
                    saved_path = default_storage.save(file_path, ContentFile(img_response.content))
                    local_url = default_storage.url(saved_path)
                    
                    processed_images.append({
                        'original_url': img_url,
                        'local_url': local_url,
                        'local_path': saved_path,
                        'alt_text': alt_text,
                        'title_text': title_text,
                        'filename': filename,
                        'width': img_width,
                        'height': img_height,
                        'dimensions': f"{img_width}x{img_height}"
                    })
                    
                    logger.info(f"Imagen extraída y guardada: {filename}")
                    
                except Exception as e:
                    logger.warning(f"Error procesando imagen {img_url}: {e}")
                    continue
                    
            except Exception as e:
                logger.warning(f"Error con imagen {i}: {e}")
                continue
        
        logger.info(f"Se procesaron {len(processed_images)} imágenes de {len(img_tags)} encontradas")
        return processed_images
        
    except Exception as e:
        logger.error(f"Error extrayendo imágenes de {url}: {e}")
        return []

def insert_images_in_content(content: str, images: list) -> str:
    """
    Inserta imágenes en el contenido HTML del post de manera inteligente.
    
    Args:
        content (str): Contenido HTML del post
        images (list): Lista de imágenes procesadas
        
    Returns:
        str: Contenido con imágenes insertadas
    """
    try:
        if not images:
            return content
        
        # Parsear el contenido HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Encontrar párrafos donde insertar imágenes
        paragraphs = soup.find_all('p')
        
        if not paragraphs:
            # Si no hay párrafos, insertar al final
            for img_data in images:
                img_html = create_image_html(img_data)
                content += f"\n\n{img_html}"
            return content
        
        # Calcular posiciones para insertar imágenes
        total_paragraphs = len(paragraphs)
        images_to_insert = min(len(images), 3)  # Máximo 3 imágenes en el contenido
        
        if total_paragraphs >= 3:
            # Insertar imágenes distribuidas a lo largo del contenido
            positions = []
            if images_to_insert >= 1:
                positions.append(total_paragraphs // 3)  # Primera tercera parte
            if images_to_insert >= 2:
                positions.append(2 * total_paragraphs // 3)  # Segunda tercera parte
            if images_to_insert >= 3:
                positions.append(total_paragraphs - 1)  # Cerca del final
        else:
            # Pocos párrafos, insertar después del primero
            positions = [1] if total_paragraphs > 1 else [0]
        
        # Insertar imágenes en las posiciones calculadas
        for i, pos in enumerate(positions[:len(images)]):
            if pos < len(paragraphs):
                img_html = create_image_html(images[i])
                img_tag = BeautifulSoup(img_html, 'html.parser')
                
                # Insertar después del párrafo
                paragraphs[pos].insert_after(img_tag)
        
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error insertando imágenes en contenido: {e}")
        return content

def create_image_html(img_data: dict) -> str:
    """
    Crea HTML para una imagen con el formato adecuado para CKEditor.
    
    Args:
        img_data (dict): Datos de la imagen
        
    Returns:
        str: HTML de la imagen
    """
    alt_text = img_data.get('alt_text', 'Imagen del artículo')
    title_text = img_data.get('title_text', '')
    local_url = img_data.get('local_url', '')
    
    # Crear HTML responsivo para la imagen
    html = f'''
    <figure style="text-align: center; margin: 20px 0;">
        <img src="{local_url}" 
             alt="{alt_text}" 
             title="{title_text}"
             style="max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" />
        {f'<figcaption style="font-style: italic; color: #666; margin-top: 8px; font-size: 0.9em;">{alt_text}</figcaption>' if alt_text else ''}
    </figure>
    '''
    
    return html.strip()

def generate_complete_post(url=None, title=None, rewrite_prompt=None, tag_prompt=None, 
                         extract_images=False, max_images=5, 
                         progress_callback=None, **kwargs):
    """
    Genera un post completo usando IA.
    
    Returns:
        dict: Diccionario con el resultado de la generación
    """
    try:
        if progress_callback:
            progress_callback("Iniciando generación de post...", 0)
        
        result = {
            'success': True,
            'title': '',
            'content': '',
            'tags': [],
            'reading_time': 1,
            'extracted_images': [],
            'suggested_cover_image': None,
            'available_cover_images': []
        }
        
        # Extraer contenido de URL si se proporciona
        if url:
            if progress_callback:
                progress_callback("Extrayendo contenido de URL...", 10)
            
            extraction_result = extract_content_from_url(url)
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': extraction_result['error']
                }
            
            # Usar título extraído si no se proporciona uno
            if not title:
                result['title'] = extraction_result['title']
            else:
                result['title'] = title
            
            content = extraction_result['content']
        else:
            if not title:
                return {
                    'success': False,
                    'error': 'Se requiere una URL o un título para generar el post'
                }
            
            result['title'] = title
            content = f"Crear contenido sobre: {title}"
        
        # Reescribir contenido con IA
        if progress_callback:
            progress_callback("Reescribiendo contenido...", 30)
        
        rewrite_result = rewrite_content_with_ai(content, rewrite_prompt, progress_callback)
        if not rewrite_result['success']:
            return {
                'success': False,
                'error': rewrite_result['error']
            }
        
        result['content'] = rewrite_result['content']
        
        # Generar tags
        if progress_callback:
            progress_callback("Generando tags...", 70)
        
        tags_result = generate_tags_with_ai(result['content'], progress_callback)
        if tags_result['success']:
            result['tags'] = tags_result['tags']
        else:
            # Tags por defecto si falla la generación
            result['tags'] = ['tecnología', 'blog', 'desarrollo']
        
        # Calcular tiempo de lectura
        result['reading_time'] = calculate_reading_time(result['content'])
        
        # Extraer y procesar imágenes del contenido si se solicita
        if extract_images and url:
            if progress_callback:
                progress_callback("Extrayendo imágenes del contenido...", 80)
            
            try:
                prioritize_large = kwargs.get('prioritize_large_images', True)
                extracted_images = extract_and_process_images(url, max_images, prioritize_large)
                result['extracted_images'] = extracted_images
                
                # Insertar imágenes en el contenido si se encontraron
                if extracted_images:
                    result['content'] = insert_images_in_content(result['content'], extracted_images)
                    result['available_cover_images'] = extracted_images  # Todas las imágenes disponibles para portada
                    logger.info(f"Se insertaron {len(extracted_images)} imágenes en el contenido")
                    logger.info(f"Disponibles {len(extracted_images)} imágenes para seleccionar como portada")
                else:
                    logger.info("No se encontraron imágenes para extraer")
                    
            except Exception as e:
                logger.warning(f"Error extrayendo imágenes: {e}")
                result['extracted_images'] = []
        
        # Sugerir imagen de portada de las extraídas si hay disponibles
        if extract_images and result.get('extracted_images'):
            # Seleccionar la primera imagen como sugerencia de portada
            first_image = result['extracted_images'][0]
            result['suggested_cover_image'] = {
                'url': first_image['local_url'],
                'path': first_image['local_path'],
                'alt_text': first_image['alt_text'],
                'filename': first_image['filename']
            }
            logger.info(f"Imagen de portada sugerida: {first_image['filename']}")
        else:
            result['suggested_cover_image'] = None
        
        if progress_callback:
            progress_callback("Post generado exitosamente", 100)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en generate_complete_post: {e}")
        return {
            'success': False,
            'error': f'Error generando post: {str(e)}'
        }