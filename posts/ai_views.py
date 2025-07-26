"""
Vistas optimizadas para generación de posts con IA.
"""

import json
import logging
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from .ai_generator_optimized import generate_complete_post_optimized
from .models import Post
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def ai_post_generator_view(request):
    """
    Vista optimizada para generar posts con IA.
    Maneja timeouts y memoria de manera eficiente.
    """
    try:
        # Parsear datos de la solicitud
        data = json.loads(request.body)
        
        url = data.get('url', '').strip()
        title = data.get('title', '').strip()
        rewrite_prompt = data.get('rewrite_prompt', '').strip()
        extract_images = data.get('extract_images', True)
        max_images = min(int(data.get('max_images', 3)), 5)  # Máximo 5 imágenes
        generate_cover = data.get('generate_cover_image', False)
        
        # Validación básica
        if not url and not title:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere una URL o un título para generar el post'
            }, status=400)
        
        # Callback para progreso (se puede extender para WebSockets)
        progress_data = {'current': 0, 'message': 'Iniciando...'}
        
        def progress_callback(message, progress):
            progress_data['current'] = progress
            progress_data['message'] = message
            logger.info(f"Progreso IA: {progress}% - {message}")
        
        # Generar post con versión optimizada
        result = generate_complete_post_optimized(
            url=url,
            title=title,
            rewrite_prompt=rewrite_prompt,
            extract_images=extract_images,
            max_images=max_images,
            generate_cover_image=generate_cover,
            progress_callback=progress_callback,
            prioritize_large_images=True
        )
        
        if result['success']:
            # Crear el post en la base de datos
            try:
                post = Post.objects.create(
                    title=result['title'],
                    content=result['content'],
                    author=request.user,
                    status='draft',  # Crear como borrador
                    reading_time=result.get('reading_time', 5)
                )
                
                # Añadir tags
                if result.get('tags'):
                    post.tags.add(*result['tags'])
                
                # Añadir información del post creado
                result['post_id'] = post.id
                result['post_url'] = post.get_absolute_url()
                result['edit_url'] = f"/post/{post.author.username}/{post.slug}/editar/"
                
                logger.info(f"Post generado exitosamente: {post.id} por {request.user.username}")
                
            except Exception as e:
                logger.error(f"Error creando post en BD: {e}")
                result['warning'] = f"Post generado pero no se pudo guardar: {str(e)}"
        
        return JsonResponse(result)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos JSON inválidos'
        }, status=400)
        
    except Exception as e:
        logger.error(f"Error en generación de post IA: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
@login_required
def ai_post_generator_simple_view(request):
    """
    Vista simplificada para generación rápida de posts.
    """
    try:
        data = json.loads(request.body)
        title = data.get('title', '').strip()
        
        if not title:
            return JsonResponse({
                'success': False,
                'error': 'Se requiere un título'
            }, status=400)
        
        # Generar contenido simple sin imágenes
        result = generate_complete_post_optimized(
            title=title,
            extract_images=False,
            max_images=0,
            generate_cover_image=False
        )
        
        return JsonResponse(result)
        
    except Exception as e:
        logger.error(f"Error en generación simple: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error: {str(e)}'
        }, status=500)

class AIPostGeneratorStreamView(View):
    """
    Vista para streaming de progreso en tiempo real.
    """
    
    @method_decorator(login_required)
    def post(self, request):
        """Genera post con streaming de progreso."""
        
        def generate_with_progress():
            """Generador que yield progreso en tiempo real."""
            try:
                data = json.loads(request.body)
                
                def progress_callback(message, progress):
                    progress_data = {
                        'type': 'progress',
                        'message': message,
                        'progress': progress
                    }
                    yield f"data: {json.dumps(progress_data)}\n\n"
                
                # Generar post
                result = generate_complete_post_optimized(
                    url=data.get('url'),
                    title=data.get('title'),
                    progress_callback=progress_callback
                )
                
                # Enviar resultado final
                final_data = {
                    'type': 'complete',
                    'result': result
                }
                yield f"data: {json.dumps(final_data)}\n\n"
                
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'error': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        response = StreamingHttpResponse(
            generate_with_progress(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        
        return response