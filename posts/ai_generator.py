import os
import re
import uuid
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from .models import AIModel

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
        return 'gemini-1.5-flash'  # Modelo por defecto

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
    Extrae imágenes de una URL y devuelve información sobre ellas.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        images = []
        img_tags = soup.find_all('img')
        
        for img in img_tags[:max_images]:
            src = img.get('src')
            alt = img.get('alt', '')
            
            if src:
                # Convertir URL relativa a absoluta
                if not src.startswith(('http://', 'https://')):
                    src = urljoin(url, src)
                
                images.append({
                    'src': src,
                    'alt': alt,
                    'title': img.get('title', alt)
                })
        
        return images
    
    except requests.RequestException as e:
        print(f"Error al extraer imágenes: {e}")
        return []

import os

def download_image(image_url: str, folder: str = 'ai_posts/images/') -> str:
    """
    Descarga una imagen y la guarda en el almacenamiento de Django.
    Retorna la URL de la imagen guardada.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

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

def generate_complete_post(url: str, rewrite_prompt: str, extract_images: bool = True, max_images: int = 5) -> dict:
    """
    Función principal que combina toda la funcionalidad para generar un post completo.
    """
    # Extraer contenido de la URL
    url_data = extract_content_from_url(url)
    
    if not url_data['content']:
        return {
            'success': False,
            'error': 'No se pudo extraer contenido de la URL'
        }
    
    # Extraer imágenes si está habilitado
    images_data = []
    if extract_images:
        images_info = extract_images_from_url(url, max_images)
        for img_info in images_info:
            local_url = download_image(img_info['src'])
            if local_url:
                img_info['local_url'] = local_url
                images_data.append(img_info)
    
    # Generar contenido con AI
    ai_result = rewrite_content_with_ai_advanced(
        url_data['content'], 
        rewrite_prompt, 
        url_data['links']
    )
    
    # Procesar imágenes en el contenido
    final_content = process_images_in_content(ai_result['content'], images_data)
    
    return {
        'success': True,
        'title': ai_result['title'],
        'content': final_content,
        'tags': ai_result['tags'],
        'original_url': url,
        'extracted_links': url_data['links'],
        'images': images_data,
        'raw_ai_response': ai_result['raw_response']
    }
