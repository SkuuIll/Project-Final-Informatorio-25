"""
Views for image selection and management.
"""

import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.contrib import messages

from ..image_generation import ImageSelector
import logging

logger = logging.getLogger(__name__)


@login_required
def image_gallery_view(request):
    """
    Vista principal de la galería de imágenes.
    """
    # Obtener parámetros de filtrado
    search_query = request.GET.get('search', '')
    folder_filter = request.GET.get('folder', '')
    suitable_only = request.GET.get('suitable_only', 'false').lower() == 'true'
    page = request.GET.get('page', 1)
    
    try:
        # Obtener imágenes según filtros
        if search_query:
            images = ImageSelector.search_images(search_query, folder_filter or None)
        elif suitable_only:
            images = ImageSelector.get_suitable_cover_images()
        else:
            images = ImageSelector.get_available_images(folder_filter or None)
        
        # Paginación
        paginator = Paginator(images, 20)  # 20 imágenes por página
        page_obj = paginator.get_page(page)
        
        # Obtener estadísticas
        stats = ImageSelector.get_image_stats()
        
        # Obtener categorías para el filtro
        categories = ImageSelector.get_images_by_category()
        
        context = {
            'images': page_obj,
            'stats': stats,
            'categories': categories,
            'search_query': search_query,
            'folder_filter': folder_filter,
            'suitable_only': suitable_only,
            'total_images': len(images),
        }
        
        return render(request, 'posts/image_gallery.html', context)
        
    except Exception as e:
        logger.error(f"Error in image gallery view: {e}")
        messages.error(request, f"Error al cargar la galería de imágenes: {str(e)}")
        
        return render(request, 'posts/image_gallery.html', {
            'images': [],
            'stats': {'total_images': 0, 'suitable_for_cover': 0, 'total_size_mb': 0},
            'categories': {},
            'error': str(e)
        })


@login_required
@require_http_methods(["GET"])
def api_get_images(request):
    """
    API endpoint para obtener imágenes (AJAX).
    """
    try:
        # Parámetros de la petición
        search = request.GET.get('search', '')
        folder = request.GET.get('folder', '')
        suitable_only = request.GET.get('suitable_only', 'false').lower() == 'true'
        limit = min(int(request.GET.get('limit', 50)), 100)  # Máximo 100
        
        # Obtener imágenes
        if search:
            images = ImageSelector.search_images(search, folder or None)
        elif suitable_only:
            images = ImageSelector.get_suitable_cover_images(limit=limit)
        else:
            images = ImageSelector.get_available_images(folder or None)
        
        # Limitar resultados
        images = images[:limit]
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'images': images,
            'total': len(images),
            'stats': ImageSelector.get_image_stats()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in API get images: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'images': [],
            'total': 0
        })


@login_required
@require_http_methods(["POST"])
def api_validate_image(request):
    """
    API endpoint para validar selección de imagen.
    """
    try:
        data = json.loads(request.body)
        image_path = data.get('image_path', '')
        
        if not image_path:
            return JsonResponse({
                'success': False,
                'error': 'No se proporcionó ruta de imagen'
            })
        
        # Validar imagen
        is_valid, error_message = ImageSelector.validate_image_selection(image_path)
        
        response_data = {
            'success': True,
            'is_valid': is_valid,
            'error_message': error_message
        }
        
        if is_valid:
            # Obtener información adicional de la imagen
            images = ImageSelector.get_available_images()
            selected_image = next((img for img in images if img['path'] == image_path), None)
            
            if selected_image:
                response_data['image_info'] = selected_image
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in API validate image: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'is_valid': False
        })


@login_required
def image_selector_modal(request):
    """
    Vista para el modal de selección de imágenes.
    """
    try:
        # Obtener solo imágenes adecuadas para portada
        suitable_images = ImageSelector.get_suitable_cover_images(limit=30)
        recent_images = ImageSelector.get_recent_images(limit=20)
        
        # Obtener categorías
        categories = ImageSelector.get_images_by_category()
        
        context = {
            'suitable_images': suitable_images,
            'recent_images': recent_images,
            'categories': categories,
            'stats': ImageSelector.get_image_stats()
        }
        
        return render(request, 'posts/partials/image_selector_modal.html', context)
        
    except Exception as e:
        logger.error(f"Error in image selector modal: {e}")
        return render(request, 'posts/partials/image_selector_modal.html', {
            'error': str(e),
            'suitable_images': [],
            'recent_images': [],
            'categories': {}
        })


@login_required
def image_preview(request, image_path):
    """
    Vista para previsualizar una imagen específica.
    """
    try:
        # Validar que la imagen existe y es válida
        is_valid, error = ImageSelector.validate_image_selection(image_path)
        
        if not is_valid:
            return JsonResponse({
                'success': False,
                'error': error
            })
        
        # Obtener información de la imagen
        images = ImageSelector.get_available_images()
        image_info = next((img for img in images if img['path'] == image_path), None)
        
        if not image_info:
            return JsonResponse({
                'success': False,
                'error': 'Imagen no encontrada'
            })
        
        return JsonResponse({
            'success': True,
            'image': image_info
        })
        
    except Exception as e:
        logger.error(f"Error in image preview: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })