"""
Vista para la galería de administración de imágenes.
"""

import os
import json
import logging
from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Q
from ..image_generation.image_selector import ImageSelector
from ..utils import safe_get_image_url, validate_image_file

logger = logging.getLogger(__name__)

@staff_member_required
def image_gallery_view(request):
    """
    Vista principal de la galería de imágenes.
    """
    # Obtener parámetros de filtrado
    folder_filter = request.GET.get('folder', '')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'date')  # date, name, size
    page = request.GET.get('page', 1)
    
    try:
        # Obtener todas las imágenes
        if search_query:
            images = ImageSelector.search_images(search_query, folder_filter or None)
        else:
            images = ImageSelector.get_available_images(folder_filter or None)
        
        # Aplicar ordenamiento
        if sort_by == 'name':
            images.sort(key=lambda x: x['filename'].lower())
        elif sort_by == 'size':
            images.sort(key=lambda x: x.get('size_bytes', 0), reverse=True)
        else:  # date (default)
            images.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
        
        # Paginación
        paginator = Paginator(images, 24)  # 24 imágenes por página
        page_obj = paginator.get_page(page)
        
        # Obtener estadísticas
        stats = ImageSelector.get_image_stats()
        
        # Obtener carpetas disponibles
        folders = set()
        for image in images:
            folders.add(image.get('folder', ''))
        folders = sorted(list(folders))
        
        context = {
            'images': page_obj,
            'stats': stats,
            'folders': folders,
            'current_folder': folder_filter,
            'search_query': search_query,
            'sort_by': sort_by,
            'total_images': len(images),
        }
        
        return render(request, 'admin/posts/image_gallery.html', context)
        
    except Exception as e:
        logger.error(f"Error in image gallery view: {e}")
        messages.error(request, f"Error cargando la galería: {str(e)}")
        return render(request, 'admin/posts/image_gallery.html', {
            'images': [],
            'stats': {},
            'folders': [],
            'error': str(e)
        })

@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def delete_image_ajax(request):
    """
    Vista AJAX para eliminar una imagen.
    """
    try:
        data = json.loads(request.body)
        image_path = data.get('image_path')
        
        if not image_path:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó la ruta de la imagen'
            })
        
        # Validar que la imagen existe
        if not default_storage.exists(image_path):
            return JsonResponse({
                'success': False,
                'error': 'La imagen no existe'
            })
        
        # Validar que está en una carpeta permitida
        allowed_folders = [
            'ai_posts/content/',
            'ai_posts/covers/',
            'ai_posts/images/',
            'post_images/',
            'uploads/',
            'images/',
        ]
        
        if not any(image_path.startswith(folder) for folder in allowed_folders):
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar imágenes de esta carpeta'
            })
        
        # Eliminar la imagen
        default_storage.delete(image_path)
        
        logger.info(f"Imagen eliminada por {request.user.username}: {image_path}")
        
        return JsonResponse({
            'success': True,
            'message': 'Imagen eliminada correctamente'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Error deleting image: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error eliminando la imagen: {str(e)}'
        })

@staff_member_required
@require_http_methods(["POST"])
@csrf_exempt
def bulk_delete_images_ajax(request):
    """
    Vista AJAX para eliminar múltiples imágenes.
    """
    try:
        data = json.loads(request.body)
        image_paths = data.get('image_paths', [])
        
        if not image_paths:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionaron imágenes para eliminar'
            })
        
        deleted_count = 0
        errors = []
        
        for image_path in image_paths:
            try:
                if default_storage.exists(image_path):
                    default_storage.delete(image_path)
                    deleted_count += 1
                else:
                    errors.append(f"No existe: {image_path}")
            except Exception as e:
                errors.append(f"Error con {image_path}: {str(e)}")
        
        logger.info(f"Eliminación masiva por {request.user.username}: {deleted_count} imágenes")
        
        return JsonResponse({
            'success': True,
            'deleted_count': deleted_count,
            'errors': errors,
            'message': f'Se eliminaron {deleted_count} imágenes'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        })
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error en eliminación masiva: {str(e)}'
        })

@staff_member_required
def image_details_ajax(request, image_path):
    """
    Vista AJAX para obtener detalles de una imagen.
    """
    try:
        # Decodificar la ruta (viene URL encoded)
        import urllib.parse
        image_path = urllib.parse.unquote(image_path)
        
        if not default_storage.exists(image_path):
            return JsonResponse({
                'success': False,
                'error': 'La imagen no existe'
            })
        
        # Obtener información detallada
        try:
            file_stats = default_storage.get_created_time(image_path)
            modified_time = file_stats.timestamp() if file_stats else 0
            created_date = datetime.fromtimestamp(modified_time).strftime('%d/%m/%Y %H:%M:%S')
        except:
            created_date = "No disponible"
        
        try:
            file_size = default_storage.size(image_path)
            size_mb = round(file_size / (1024 * 1024), 2)
        except:
            file_size = 0
            size_mb = 0
        
        # Obtener dimensiones si es posible
        try:
            from PIL import Image
            with default_storage.open(image_path, 'rb') as f:
                with Image.open(f) as img:
                    width, height = img.size
                    dimensions = f"{width}x{height}"
        except:
            dimensions = "No disponible"
        
        return JsonResponse({
            'success': True,
            'details': {
                'filename': os.path.basename(image_path),
                'path': image_path,
                'url': default_storage.url(image_path),
                'folder': os.path.dirname(image_path),
                'size_bytes': file_size,
                'size_mb': size_mb,
                'dimensions': dimensions,
                'created_date': created_date,
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting image details: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error obteniendo detalles: {str(e)}'
        })