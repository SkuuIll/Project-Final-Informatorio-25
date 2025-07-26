"""
Sistema de generación de imágenes para posts usando diferentes servicios de IA.
"""
import os
import uuid
import logging
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ImageGenerationService:
    """Clase base para servicios de generación de imágenes."""
    
    def __init__(self, name):
        self.name = name
    
    def is_available(self):
        """Verifica si el servicio está disponible."""
        return False
    
    def generate_image(self, prompt, style='professional', title='', size='1024x1024'):
        """
        Genera una imagen basada en el prompt.
        
        Returns:
            tuple: (success: bool, image_url: str, error: str)
        """
        return False, None, "Servicio no implementado"
    
    def get_service_name(self):
        """Obtiene el nombre legible del servicio."""
        return self.name.title()
    
    def get_supported_parameters(self):
        """Obtiene los parámetros soportados por el servicio."""
        return {
            'size': {
                'options': ['1024x1024', '512x512', '768x768'],
                'default': '1024x1024'
            },
            'style': {
                'options': ['professional', 'modern', 'creative', 'minimalist'],
                'default': 'professional'
            }
        }

class GeminiImageService(ImageGenerationService):
    """Servicio de generación de imágenes usando Google Gemini."""
    
    def __init__(self):
        super().__init__('gemini')
        self.api_key = os.getenv('GOOGLE_API_KEY')
    
    def is_available(self):
        """Verifica si Gemini está disponible."""
        return bool(self.api_key)
    
    def get_service_name(self):
        """Nombre legible del servicio."""
        return "Google Gemini (Placeholder con IA)"
    
    def generate_image(self, prompt, style='professional', title='', size='1024x1024'):
        """
        Genera una imagen usando Gemini (actualmente genera placeholder).
        
        Nota: Gemini no tiene generación de imágenes directa, así que creamos
        un placeholder con descripción generada por IA.
        """
        try:
            if not self.is_available():
                return False, None, "API key de Google no configurada"
            
            # Configurar Gemini con el modelo 2.5-pro
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.5-pro')
            
            # Generar descripción de imagen avanzada con Gemini 2.5-pro
            image_description_prompt = f"""
            Eres un diseñador gráfico experto especializado en crear imágenes de portada para blogs. 
            
            Crea una descripción detallada y visual para una imagen de portada sobre: "{title}"
            
            Contexto del prompt: {prompt}
            Estilo solicitado: {style}
            
            Tu descripción debe incluir:
            1. **Composición visual**: Disposición de elementos, perspectiva, encuadre
            2. **Paleta de colores**: Colores específicos con códigos hex si es posible
            3. **Elementos gráficos**: Formas, iconos, símbolos, texturas
            4. **Tipografía**: Estilo de texto, jerarquía visual
            5. **Ambiente**: Mood, sensación, estilo artístico
            6. **Detalles técnicos**: Efectos, sombras, gradientes, iluminación
            
            Responde SOLO con la descripción visual detallada, sin explicaciones adicionales.
            Máximo 200 palabras, enfócate en elementos visuales concretos y específicos.
            """
            
            response = model.generate_content(image_description_prompt)
            description = response.text.strip() if response.text else "Imagen profesional para blog"
            
            logger.info(f"Descripción de imagen generada: {description}")
            
            # Crear imagen placeholder con la descripción
            image_url = self._create_placeholder_image(title, description, style, size)
            
            return True, image_url, None
            
        except Exception as e:
            logger.error(f"Error generando imagen con Gemini: {e}")
            return False, None, str(e)
    
    def _create_placeholder_image(self, title, description, style, size):
        """Crea una imagen placeholder avanzada con información generada por Gemini 2.5-pro."""
        try:
            # Parsear tamaño
            width, height = map(int, size.split('x'))
            
            # Crear imagen base
            image = Image.new('RGB', (width, height), color='#f0f8ff')
            draw = ImageDraw.Draw(image)
            
            # Extraer colores de la descripción si es posible
            extracted_colors = self._extract_colors_from_description(description)
            
            # Esquemas de colores mejorados según el estilo
            colors = {
                'professional': {
                    'bg': extracted_colors.get('primary', '#1e3a8a'), 
                    'secondary': extracted_colors.get('secondary', '#3b82f6'),
                    'text': '#ffffff', 
                    'accent': extracted_colors.get('accent', '#60a5fa')
                },
                'creative': {
                    'bg': extracted_colors.get('primary', '#7c3aed'), 
                    'secondary': extracted_colors.get('secondary', '#a855f7'),
                    'text': '#ffffff', 
                    'accent': extracted_colors.get('accent', '#ec4899')
                },
                'modern': {
                    'bg': extracted_colors.get('primary', '#0f172a'), 
                    'secondary': extracted_colors.get('secondary', '#1e293b'),
                    'text': '#f8fafc', 
                    'accent': extracted_colors.get('accent', '#06b6d4')
                },
                'minimalist': {
                    'bg': extracted_colors.get('primary', '#f8fafc'), 
                    'secondary': extracted_colors.get('secondary', '#e2e8f0'),
                    'text': '#1e293b', 
                    'accent': extracted_colors.get('accent', '#64748b')
                },
                'tech': {
                    'bg': extracted_colors.get('primary', '#000000'), 
                    'secondary': extracted_colors.get('secondary', '#1a1a1a'),
                    'text': '#00ff41', 
                    'accent': extracted_colors.get('accent', '#0099ff')
                },
            }
            
            color_scheme = colors.get(style, colors['professional'])
            
            # Crear fondo con gradiente avanzado basado en la descripción
            self._create_advanced_background(draw, width, height, color_scheme, description)
            
            # Agregar elementos gráficos basados en la descripción
            self._add_graphic_elements(draw, width, height, color_scheme, description)
            
            # Intentar cargar fuente
            try:
                # Fuentes comunes en Windows
                font_paths = [
                    'C:/Windows/Fonts/arial.ttf',
                    'C:/Windows/Fonts/calibri.ttf',
                    'arial.ttf',
                    'calibri.ttf'
                ]
                
                title_font = None
                desc_font = None
                
                for font_path in font_paths:
                    try:
                        title_font = ImageFont.truetype(font_path, 48)
                        desc_font = ImageFont.truetype(font_path, 24)
                        break
                    except:
                        continue
                
                if not title_font:
                    title_font = ImageFont.load_default()
                    desc_font = ImageFont.load_default()
                    
            except Exception as e:
                logger.warning(f"Error cargando fuente: {e}")
                title_font = ImageFont.load_default()
                desc_font = ImageFont.load_default()
            
            # Dibujar título
            title_text = title[:50] + "..." if len(title) > 50 else title
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            
            title_x = (width - title_width) // 2
            title_y = height // 3
            
            # Sombra del título
            draw.text((title_x + 2, title_y + 2), title_text, fill='#000000', font=title_font)
            # Título principal
            draw.text((title_x, title_y), title_text, fill=color_scheme['text'], font=title_font)
            
            # Dibujar descripción (dividida en líneas)
            desc_words = description.split()
            lines = []
            current_line = []
            
            for word in desc_words:
                test_line = ' '.join(current_line + [word])
                test_bbox = draw.textbbox((0, 0), test_line, font=desc_font)
                test_width = test_bbox[2] - test_bbox[0]
                
                if test_width <= width - 100:  # Margen de 50px a cada lado
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Limitar a 3 líneas
            lines = lines[:3]
            
            desc_y = title_y + title_height + 40
            for i, line in enumerate(lines):
                line_bbox = draw.textbbox((0, 0), line, font=desc_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = (width - line_width) // 2
                
                # Sombra
                draw.text((line_x + 1, desc_y + 1), line, fill='#000000', font=desc_font)
                # Texto principal
                draw.text((line_x, desc_y), line, fill=color_scheme['accent'], font=desc_font)
                desc_y += 35
            
            # Agregar elemento decorativo
            accent_color = color_scheme['accent']
            accent_rgb = tuple(int(accent_color[i:i+2], 16) for i in (1, 3, 5))
            
            # Líneas decorativas
            draw.rectangle([width//4, height - 100, 3*width//4, height - 95], fill=accent_rgb)
            draw.rectangle([width//3, height - 90, 2*width//3, height - 85], fill=accent_rgb)
            
            # Guardar imagen
            image_buffer = BytesIO()
            image.save(image_buffer, format='JPEG', quality=90)
            image_buffer.seek(0)
            
            # Generar nombre único
            image_filename = f"cover_{uuid.uuid4().hex[:8]}.jpg"
            image_path = f"ai_posts/covers/{image_filename}"
            
            # Guardar en storage
            saved_path = default_storage.save(image_path, ContentFile(image_buffer.getvalue()))
            image_url = default_storage.url(saved_path)
            
            logger.info(f"Imagen placeholder avanzada creada con Gemini 2.5-pro: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Error creando imagen placeholder: {e}")
            raise
    
    def _extract_colors_from_description(self, description):
        """Extrae colores mencionados en la descripción de Gemini 2.5-pro."""
        import re
        colors = {}
        
        # Buscar códigos hex en la descripción
        hex_colors = re.findall(r'#[0-9a-fA-F]{6}', description)
        if hex_colors:
            colors['primary'] = hex_colors[0]
            if len(hex_colors) > 1:
                colors['secondary'] = hex_colors[1]
            if len(hex_colors) > 2:
                colors['accent'] = hex_colors[2]
        
        # Buscar nombres de colores comunes
        color_map = {
            'azul': '#3b82f6', 'blue': '#3b82f6',
            'rojo': '#ef4444', 'red': '#ef4444',
            'verde': '#22c55e', 'green': '#22c55e',
            'morado': '#8b5cf6', 'purple': '#8b5cf6',
            'naranja': '#f97316', 'orange': '#f97316',
            'amarillo': '#eab308', 'yellow': '#eab308',
            'rosa': '#ec4899', 'pink': '#ec4899',
            'gris': '#6b7280', 'gray': '#6b7280',
            'negro': '#000000', 'black': '#000000',
            'blanco': '#ffffff', 'white': '#ffffff'
        }
        
        description_lower = description.lower()
        for color_name, hex_value in color_map.items():
            if color_name in description_lower:
                if 'primary' not in colors:
                    colors['primary'] = hex_value
                elif 'secondary' not in colors:
                    colors['secondary'] = hex_value
                elif 'accent' not in colors:
                    colors['accent'] = hex_value
                    break
        
        return colors
    
    def _create_advanced_background(self, draw, width, height, color_scheme, description):
        """Crea un fondo avanzado basado en la descripción de Gemini 2.5-pro."""
        # Determinar tipo de fondo basado en la descripción
        description_lower = description.lower()
        
        if 'gradiente' in description_lower or 'gradient' in description_lower:
            self._create_gradient_background(draw, width, height, color_scheme)
        elif 'geométrico' in description_lower or 'geometric' in description_lower:
            self._create_geometric_background(draw, width, height, color_scheme)
        elif 'abstracto' in description_lower or 'abstract' in description_lower:
            self._create_abstract_background(draw, width, height, color_scheme)
        else:
            # Fondo gradiente por defecto mejorado
            self._create_gradient_background(draw, width, height, color_scheme)
    
    def _create_gradient_background(self, draw, width, height, color_scheme):
        """Crea un fondo con gradiente suave."""
        bg_color = color_scheme['bg']
        secondary_color = color_scheme['secondary']
        
        # Convertir colores hex a RGB
        bg_rgb = tuple(int(bg_color[i:i+2], 16) for i in (1, 3, 5))
        sec_rgb = tuple(int(secondary_color[i:i+2], 16) for i in (1, 3, 5))
        
        for y in range(height):
            # Gradiente diagonal
            for x in range(width):
                alpha_y = y / height
                alpha_x = x / width
                alpha = (alpha_y + alpha_x) / 2
                
                r = int(bg_rgb[0] + (sec_rgb[0] - bg_rgb[0]) * alpha)
                g = int(bg_rgb[1] + (sec_rgb[1] - bg_rgb[1]) * alpha)
                b = int(bg_rgb[2] + (sec_rgb[2] - bg_rgb[2]) * alpha)
                
                draw.point((x, y), fill=(r, g, b))
    
    def _create_geometric_background(self, draw, width, height, color_scheme):
        """Crea un fondo con elementos geométricos."""
        # Fondo base
        bg_rgb = tuple(int(color_scheme['bg'][i:i+2], 16) for i in (1, 3, 5))
        draw.rectangle([0, 0, width, height], fill=bg_rgb)
        
        # Elementos geométricos
        accent_rgb = tuple(int(color_scheme['accent'][i:i+2], 16) for i in (1, 3, 5))
        
        # Círculos decorativos
        for i in range(5):
            x = (width // 6) * (i + 1)
            y = height // 4
            radius = 30 + i * 10
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                        outline=accent_rgb, width=2)
        
        # Líneas diagonales
        for i in range(0, width, 100):
            draw.line([(i, 0), (i + height//2, height)], 
                     fill=accent_rgb, width=1)
    
    def _create_abstract_background(self, draw, width, height, color_scheme):
        """Crea un fondo abstracto."""
        import random
        
        # Fondo base
        bg_rgb = tuple(int(color_scheme['bg'][i:i+2], 16) for i in (1, 3, 5))
        draw.rectangle([0, 0, width, height], fill=bg_rgb)
        
        # Formas abstractas
        colors = [color_scheme['secondary'], color_scheme['accent']]
        
        for _ in range(8):
            color = random.choice(colors)
            color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            
            # Formas aleatorias
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = x1 + random.randint(50, 200)
            y2 = y1 + random.randint(50, 200)
            
            # Transparencia simulada
            alpha = 0.3
            blended_color = tuple(int(bg_rgb[i] * (1-alpha) + color_rgb[i] * alpha) for i in range(3))
            
            draw.ellipse([x1, y1, x2, y2], fill=blended_color)
    
    def _add_graphic_elements(self, draw, width, height, color_scheme, description):
        """Agrega elementos gráficos basados en la descripción."""
        description_lower = description.lower()
        accent_rgb = tuple(int(color_scheme['accent'][i:i+2], 16) for i in (1, 3, 5))
        
        # Elementos específicos basados en palabras clave
        if 'tecnología' in description_lower or 'tech' in description_lower:
            self._add_tech_elements(draw, width, height, accent_rgb)
        elif 'red' in description_lower or 'conexión' in description_lower:
            self._add_network_elements(draw, width, height, accent_rgb)
        elif 'datos' in description_lower or 'data' in description_lower:
            self._add_data_elements(draw, width, height, accent_rgb)
    
    def _add_tech_elements(self, draw, width, height, color):
        """Agrega elementos tecnológicos."""
        # Circuitos simples
        for i in range(3):
            y = height // 4 * (i + 1)
            draw.line([(50, y), (width - 50, y)], fill=color, width=2)
            
            # Nodos en el circuito
            for x in range(100, width - 100, 150):
                draw.ellipse([x-5, y-5, x+5, y+5], fill=color)
    
    def _add_network_elements(self, draw, width, height, color):
        """Agrega elementos de red/conexión."""
        import random
        
        # Nodos de red
        nodes = []
        for _ in range(6):
            x = random.randint(100, width - 100)
            y = random.randint(100, height - 100)
            nodes.append((x, y))
            draw.ellipse([x-8, y-8, x+8, y+8], fill=color)
        
        # Conexiones entre nodos
        for i, node1 in enumerate(nodes):
            for j, node2 in enumerate(nodes[i+1:], i+1):
                if random.random() > 0.6:  # Solo algunas conexiones
                    draw.line([node1, node2], fill=color, width=1)
    
    def _add_data_elements(self, draw, width, height, color):
        """Agrega elementos relacionados con datos."""
        # Barras de datos
        bar_width = 20
        for i in range(5):
            x = width // 6 * (i + 1) - bar_width // 2
            bar_height = 50 + i * 30
            y = height - 100 - bar_height
            draw.rectangle([x, y, x + bar_width, height - 100], fill=color)

class PlaceholderImageService(ImageGenerationService):
    """Servicio de respaldo que genera imágenes placeholder simples."""
    
    def __init__(self):
        super().__init__('placeholder')
    
    def is_available(self):
        """Siempre disponible como respaldo."""
        return True
    
    def get_service_name(self):
        """Nombre legible del servicio."""
        return "Placeholder Simple"
    
    def generate_image(self, prompt, style='professional', title='', size='1024x1024'):
        """Genera una imagen placeholder simple."""
        try:
            width, height = map(int, size.split('x'))
            
            # Crear imagen simple
            image = Image.new('RGB', (width, height), color='#3498db')
            draw = ImageDraw.Draw(image)
            
            # Texto simple
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            text = title[:30] + "..." if len(title) > 30 else title
            if text:
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                text_x = (width - text_width) // 2
                text_y = (height - text_height) // 2
                
                draw.text((text_x, text_y), text, fill='white', font=font)
            
            # Guardar
            image_buffer = BytesIO()
            image.save(image_buffer, format='JPEG', quality=85)
            image_buffer.seek(0)
            
            image_filename = f"placeholder_{uuid.uuid4().hex[:8]}.jpg"
            image_path = f"ai_posts/covers/{image_filename}"
            
            saved_path = default_storage.save(image_path, ContentFile(image_buffer.getvalue()))
            image_url = default_storage.url(saved_path)
            
            return True, image_url, None
            
        except Exception as e:
            logger.error(f"Error generando placeholder: {e}")
            return False, None, str(e)

class ImageGenerationRegistry:
    """Registry para gestionar servicios de generación de imágenes."""
    
    def __init__(self):
        self.services = {}
        self._register_default_services()
    
    def _register_default_services(self):
        """Registra los servicios por defecto."""
        self.register_service(GeminiImageService())
        self.register_service(PlaceholderImageService())
        
        logger.info("Servicios de generación de imágenes registrados")
    
    def register_service(self, service):
        """Registra un servicio de generación de imágenes."""
        self.services[service.name] = service
        logger.info(f"Servicio de imagen registrado: {service.name}")
    
    def get_service(self, name):
        """Obtiene un servicio por nombre."""
        return self.services.get(name)
    
    def get_available_services(self):
        """Obtiene lista de servicios disponibles."""
        return [name for name, service in self.services.items() if service.is_available()]
    
    def get_default_service(self):
        """Obtiene el servicio por defecto disponible."""
        # Prioridad: gemini > placeholder
        for service_name in ['gemini', 'placeholder']:
            service = self.get_service(service_name)
            if service and service.is_available():
                return service
        return None

# Instancia global del registry
registry = ImageGenerationRegistry()

def generate_image_for_post(title, content_preview, style='professional', service_name='gemini'):
    """
    Función de conveniencia para generar imagen de post.
    
    Args:
        title (str): Título del post
        content_preview (str): Vista previa del contenido
        style (str): Estilo de la imagen
        service_name (str): Nombre del servicio a usar
        
    Returns:
        tuple: (success: bool, image_url: str, error: str)
    """
    try:
        service = registry.get_service(service_name)
        
        if not service:
            # Usar servicio por defecto
            service = registry.get_default_service()
            if not service:
                return False, None, "No hay servicios de imagen disponibles"
        
        if not service.is_available():
            # Intentar con servicio por defecto
            service = registry.get_default_service()
            if not service:
                return False, None, f"Servicio {service_name} no disponible y no hay alternativas"
        
        # Crear prompt para la imagen
        prompt = f"""
        Crear una imagen de portada profesional para un artículo de blog sobre: {title}
        
        La imagen debe ser:
        - {style} y atractiva
        - Relacionada con el tema del artículo
        - Adecuada para usar como imagen de cabecera
        - Con colores que transmitan {style}
        
        Contenido del artículo: {content_preview[:200]}...
        """
        
        return service.generate_image(prompt, style=style, title=title)
        
    except Exception as e:
        logger.error(f"Error en generate_image_for_post: {e}")
        return False, None, str(e)