"""
Utilidades para manejo seguro de archivos.
"""

import os
import magic
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class SecureFileValidator:
    """
    Validador de archivos con verificaciones de seguridad.
    """
    
    ALLOWED_IMAGE_TYPES = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp'
    ]
    
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_IMAGE_DIMENSIONS = (2048, 2048)
    
    @classmethod
    def validate_image(cls, uploaded_file):
        """
        Valida que el archivo sea una imagen segura.
        
        Args:
            uploaded_file: Archivo subido de Django
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # Verificar tamaño
            if uploaded_file.size > cls.MAX_FILE_SIZE:
                return False, f"El archivo es demasiado grande. Máximo permitido: {cls.MAX_FILE_SIZE // (1024*1024)}MB"
            
            # Verificar tipo MIME
            uploaded_file.seek(0)
            file_content = uploaded_file.read(1024)
            uploaded_file.seek(0)
            
            mime_type = magic.from_buffer(file_content, mime=True)
            
            if mime_type not in cls.ALLOWED_IMAGE_TYPES:
                return False, f"Tipo de archivo no permitido: {mime_type}"
            
            # Verificar que sea una imagen válida
            try:
                with Image.open(uploaded_file) as img:
                    # Verificar dimensiones
                    if img.size[0] > cls.MAX_IMAGE_DIMENSIONS[0] or img.size[1] > cls.MAX_IMAGE_DIMENSIONS[1]:
                        return False, f"Imagen demasiado grande. Máximo: {cls.MAX_IMAGE_DIMENSIONS[0]}x{cls.MAX_IMAGE_DIMENSIONS[1]}"
                    
                    # Verificar formato
                    if img.format.lower() not in ['jpeg', 'png', 'gif', 'webp']:
                        return False, "Formato de imagen no válido"
                        
            except Exception as e:
                return False, f"Archivo de imagen corrupto: {str(e)}"
            
            uploaded_file.seek(0)
            return True, "Archivo válido"
            
        except Exception as e:
            logger.error(f"Error validando archivo: {e}")
            return False, f"Error validando archivo: {str(e)}"


def secure_save_uploaded_file(uploaded_file, upload_path, validate_func=None, optimize=False):
    """
    Guarda un archivo de forma segura con validaciones.
    
    Args:
        uploaded_file: Archivo subido de Django
        upload_path: Ruta donde guardar el archivo
        validate_func: Función de validación opcional
        optimize: Si optimizar imágenes
        
    Returns:
        tuple: (success, result) donde result es la ruta del archivo o mensaje de error
    """
    try:
        # Validar archivo si se proporciona función de validación
        if validate_func:
            is_valid, error_message = validate_func(uploaded_file)
            if not is_valid:
                return False, error_message
        
        # Generar nombre de archivo seguro
        import uuid
        from django.utils.text import slugify
        
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        safe_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Crear ruta completa
        full_path = os.path.join(upload_path, safe_filename)
        
        # Optimizar imagen si se solicita
        if optimize and uploaded_file.content_type.startswith('image/'):
            try:
                optimized_file = optimize_image(uploaded_file)
                if optimized_file:
                    uploaded_file = optimized_file
            except Exception as e:
                logger.warning(f"No se pudo optimizar imagen: {e}")
        
        # Guardar archivo
        saved_path = default_storage.save(full_path, uploaded_file)
        
        logger.info(f"Archivo guardado exitosamente: {saved_path}")
        return True, saved_path
        
    except Exception as e:
        logger.error(f"Error guardando archivo: {e}")
        return False, f"Error guardando archivo: {str(e)}"


def optimize_image(uploaded_file, quality=85, max_size=(1920, 1080)):
    """
    Optimiza una imagen reduciendo su tamaño y calidad.
    
    Args:
        uploaded_file: Archivo de imagen
        quality: Calidad JPEG (1-100)
        max_size: Tamaño máximo (ancho, alto)
        
    Returns:
        BytesIO: Archivo optimizado o None si hay error
    """
    try:
        from io import BytesIO
        from django.core.files.uploadedfile import InMemoryUploadedFile
        
        with Image.open(uploaded_file) as img:
            # Convertir a RGB si es necesario
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionar si es necesario
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Guardar optimizado
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            # Crear nuevo archivo
            optimized_file = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{os.path.splitext(uploaded_file.name)[0]}.jpg",
                'image/jpeg',
                output.getbuffer().nbytes,
                None
            )
            
            return optimized_file
            
    except Exception as e:
        logger.error(f"Error optimizando imagen: {e}")
        return None


def clean_filename(filename):
    """
    Limpia un nombre de archivo para hacerlo seguro.
    
    Args:
        filename: Nombre del archivo original
        
    Returns:
        str: Nombre de archivo limpio
    """
    import re
    from django.utils.text import slugify
    
    # Obtener nombre y extensión
    name, ext = os.path.splitext(filename)
    
    # Limpiar nombre
    clean_name = slugify(name)
    
    # Si el nombre queda vacío, usar un nombre por defecto
    if not clean_name:
        clean_name = "archivo"
    
    # Limpiar extensión
    clean_ext = re.sub(r'[^a-zA-Z0-9.]', '', ext.lower())
    
    return f"{clean_name}{clean_ext}"