from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from blog.decorators import ajax_required
from django_ckeditor_5 import views as ckeditor_views
from blog.ratelimit import (
    api_rate_limit, search_rate_limit, user_action_limit as write_rate_limit,
    api_rate_limit as sensitive_rate_limit, login_rate_limit as auth_rate_limit
)
from blog.ratelimit import get_client_ip
import logging

logger = logging.getLogger('django.security')
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.views.generic.dates import ArchiveIndexView
from django.utils import timezone
from django.db import models
from .models import Post, Comment
from .forms import CommentForm, PostForm, AiPostGeneratorForm
from taggit.models import Tag
from accounts.models import Notification
from django.contrib import messages
from .ai_generator import extract_content_from_url, rewrite_content_with_ai, generate_tags_with_ai, generate_complete_post

from django.db.models import Q, Sum, Count, F
from rest_framework import viewsets
from .serializers import PostSerializer

# Imports for dashboard
from datetime import date, timedelta
import json
import os
from django.core.files.storage import default_storage




@login_required
def upload_image_view(request):
    """
    Vista para manejar la subida de imágenes desde CKEditor con seguridad avanzada.
    """
    if request.method == 'POST' and request.FILES.get('upload'):
        uploaded_file = request.FILES['upload']
        
        try:
            # Registrar intento de subida
            ip = get_client_ip(request)
            logger.info(
                f"Intento de subida de imagen: {uploaded_file.name}, tamaño={uploaded_file.size}, ip={ip}",
                extra={
                    'user_id': request.user.id,
                    'ip': ip,
                    'upload_filename': uploaded_file.name,  # Cambiado de 'filename' a 'upload_filename'
                    'filesize': uploaded_file.size,
                }
            )
            
            # Validaciones básicas
            max_size = 5 * 1024 * 1024  # 5MB
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            
            # Verificar tamaño
            if uploaded_file.size > max_size:
                return JsonResponse({
                    'error': {'message': f'El archivo es demasiado grande. Máximo permitido: 5MB'}
                }, status=400)
            
            # Verificar tipo de archivo por extensión
            file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
            if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                return JsonResponse({
                    'error': {'message': 'Tipo de archivo no permitido. Use JPG, PNG, GIF o WebP'}
                }, status=400)
            
            # Verificar content type
            if uploaded_file.content_type not in allowed_types:
                return JsonResponse({
                    'error': {'message': f'Tipo de contenido no válido: {uploaded_file.content_type}'}
                }, status=400)
            
            # Usar guardado simple y seguro
            return simple_save_image(uploaded_file)
                
        except Exception as e:
            logger.error(f"Error en upload_image_view: {e}", exc_info=True)
            return JsonResponse({
                'error': {'message': 'Error interno del servidor al subir la imagen'}
            }, status=500)
    
    return JsonResponse({'error': {'message': 'Petición no válida.'}}, status=400)


def simple_save_image(uploaded_file):
    """
    Función para guardar imágenes de forma simple y segura.
    """
    try:
        import uuid
        import os
        from django.core.files.storage import default_storage
        
        # Validaciones adicionales
        if not uploaded_file:
            return JsonResponse({
                'error': {'message': 'No se recibió ningún archivo'}
            }, status=400)
        
        # Verificar que el archivo tenga contenido
        if uploaded_file.size == 0:
            return JsonResponse({
                'error': {'message': 'El archivo está vacío'}
            }, status=400)
        
        # Generar nombre único
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        if not file_extension:
            file_extension = '.jpg'  # Extensión por defecto
            
        safe_filename = f"{uuid.uuid4().hex}{file_extension}"
        
        # Crear directorio si no existe
        upload_dir = "uploads/posts_content"
        
        # Guardar archivo
        file_path = f"{upload_dir}/{safe_filename}"
        saved_path = default_storage.save(file_path, uploaded_file)
        
        # Obtener URL completa
        file_url = default_storage.url(saved_path)
        
        # La URL ya debería ser correcta desde default_storage.url()
        # No necesitamos hacer absoluta la URL para CKEditor
        
        logger.info(f"Imagen guardada exitosamente: {saved_path}, URL: {file_url}")
        return JsonResponse({'url': file_url})
        
    except Exception as e:
        logger.error(f"Error en simple_save_image: {e}", exc_info=True)
        return JsonResponse({
            'error': {'message': f'Error guardando imagen: {str(e)}'}
        }, status=500)


@csrf_exempt
@login_required
def custom_upload_file(request):
    """
    Vista personalizada para subida de imágenes en CKEditor5.
    """
    # Log de debug para la solicitud
    logger.info(f"Solicitud de subida de imagen: método={request.method}, usuario={request.user.username}")
    logger.info(f"Archivos en request: {list(request.FILES.keys())}")
    
    if request.method == 'POST' and request.FILES.get('upload'):
        uploaded_file = request.FILES['upload']
        
        # Log detalles del archivo
        logger.info(f"Archivo recibido: nombre={uploaded_file.name}, tamaño={uploaded_file.size}, tipo={uploaded_file.content_type}")
        
        try:
            # Validaciones básicas
            max_size = 5 * 1024 * 1024  # 5MB
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'avif']
            allowed_content_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp', 'image/avif']
            
            # Verificar tamaño
            if uploaded_file.size > max_size:
                logger.warning(f"Archivo demasiado grande: {uploaded_file.size} bytes")
                return JsonResponse({
                    'error': {
                        'message': f'El archivo es demasiado grande ({uploaded_file.size} bytes). Máximo permitido: 5MB'
                    }
                }, status=400)
            
            # Verificar extensión
            file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
            if file_extension not in allowed_extensions:
                logger.warning(f"Extensión no permitida: {file_extension}")
                return JsonResponse({
                    'error': {
                        'message': f'Tipo de archivo no permitido ({file_extension}). Use JPG, PNG, GIF, WebP o AVIF'
                    }
                }, status=400)
            
            # Verificar content type
            if uploaded_file.content_type not in allowed_content_types:
                logger.warning(f"Content type no permitido: {uploaded_file.content_type}")
                return JsonResponse({
                    'error': {
                        'message': f'Tipo de contenido no válido ({uploaded_file.content_type})'
                    }
                }, status=400)
            
            # Crear directorio si no existe
            import os
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Generar nombre único
            import uuid
            safe_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Guardar archivo
            file_path = f"uploads/{safe_filename}"
            logger.info(f"Intentando guardar archivo en: {file_path}")
            
            saved_path = default_storage.save(file_path, uploaded_file)
            logger.info(f"Archivo guardado en: {saved_path}")
            
            # Obtener URL completa
            file_url = default_storage.url(saved_path)
            logger.info(f"URL generada: {file_url}")
            
            # Log exitoso
            logger.info(f"Imagen subida exitosamente: {saved_path} por usuario {request.user.username}")
            
            return JsonResponse({
                'url': file_url
            })
            
        except Exception as e:
            logger.error(f"Error subiendo imagen: {e}", exc_info=True)
            return JsonResponse({
                'error': {
                    'message': f'Hubo un problema al subir la imagen: {str(e)}'
                }
            }, status=500)
    
    logger.warning(f"Solicitud inválida: método={request.method}, archivos={list(request.FILES.keys())}")
    return JsonResponse({
        'error': {
            'message': 'Petición no válida. Método debe ser POST con archivo "upload".'
        }
    }, status=400)
   

class PostListView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "object_list"
    paginate_by = 12  # Aumentado de 6 a 12 posts por página

    def get_queryset(self):
        # Usar el manager optimizado para eliminar consultas N+1
        queryset = Post.optimized.get_queryset().published().with_relations().with_stats()
        
        # Ordenar con sticky posts primero
        return queryset.extra(
            select={'is_sticky_int': 'CASE WHEN is_sticky THEN 0 ELSE 1 END'}
        ).order_by('is_sticky_int', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the IDs of the most recent posts that have tags
        tagged_posts = Post.optimized.published().filter(tags__isnull=False).order_by('-created_at')
        # Get the tags from those posts, preserving order and uniqueness
        tag_ids = []
        for post in tagged_posts:
            for tag in post.tags.all():
                if tag.id not in tag_ids:
                    tag_ids.append(tag.id)
                if len(tag_ids) >= 6:
                    break
            if len(tag_ids) >= 6:
                break
        
        # Fetch the actual Tag objects
        context['all_tags'] = Tag.objects.filter(id__in=tag_ids).order_by('-post__created_at').distinct()[:6]
        return context


class PostListByTagView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "object_list"
    paginate_by = 12  # Consistente con PostListView

    def get_queryset(self):
        tag_slug = self.kwargs.get("tag_slug")
        # Usar el manager optimizado para posts con tag específico
        queryset = Post.optimized.with_tag(tag_slug).with_stats()
        
        # Ordenar con sticky posts primero, igual que PostListView
        return queryset.extra(
            select={'is_sticky_int': 'CASE WHEN is_sticky THEN 0 ELSE 1 END'}
        ).order_by('is_sticky_int', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get the IDs of the most recent posts that have tags
        tagged_posts = Post.objects.filter(status="published", tags__isnull=False).order_by('-created_at')
        # Get the tags from those posts, preserving order and uniqueness
        tag_ids = []
        for post in tagged_posts:
            for tag in post.tags.all():
                if tag.id not in tag_ids:
                    tag_ids.append(tag.id)
                if len(tag_ids) >= 6:
                    break
            if len(tag_ids) >= 6:
                break
        
        # Fetch the actual Tag objects
        context['all_tags'] = Tag.objects.filter(id__in=tag_ids).order_by('-post__created_at').distinct()[:6]
        return context


class TagListView(ListView):
    model = Tag
    template_name = "posts/tag_list.html"
    context_object_name = "tags"
    paginate_by = 20

    def get_queryset(self):
        tag_slug = self.kwargs.get("tag_slug")
        if tag_slug:
            tag = get_object_or_404(Tag, slug=tag_slug)
            return Post.objects.filter(tags__in=[tag], status="published").order_by(
                "-created_at"
            )
        return Post.objects.filter(status="published").order_by("-created_at")


class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    lookup_field = "slug"
    
    def get_queryset(self):
        # Usar el manager optimizado para API
        return Post.objects.filter(status='published').select_related('author').prefetch_related('tags')





class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        slug = self.kwargs.get('slug')
        post = get_object_or_404(
            Post.objects.select_related('author', 'author__profile')
                       .prefetch_related('tags', 'likes', 'favorites', 'comments__author', 'comments__likes'),
            author__username=username, 
            slug=slug
        )
        # Increment views atomically to avoid race conditions
        Post.objects.filter(pk=post.pk).update(views=F('views') + 1)
        post.refresh_from_db(fields=['views'])
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        context["comment_form"] = CommentForm()

        context['post_url'] = self.request.build_absolute_uri(post.get_absolute_url())
        
        if post.header_image:
            context['og_image_url'] = self.request.build_absolute_uri(post.header_image.url)
        else:
            context['og_image_url'] = self.request.build_absolute_uri('/static/social_banner.png')


        post_tags_ids = post.tags.values_list("id", flat=True)
        similar_posts = Post.objects.filter(tags__in=post_tags_ids).exclude(id=post.id)
        context["similar_posts"] = similar_posts.distinct().order_by("-created_at")[:4]
        context["post_tags"] = post.tags.annotate(num_times=Count('taggit_taggeditem_items')).order_by('-num_times')[:4]

        return context

    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        form = CommentForm(request.POST)
        if form.is_valid():
            post_obj = self.get_object()
            comment = form.save(commit=False)
            comment.post = post_obj
            comment.author = request.user
            comment.save()

            if post_obj.author != request.user:
                Notification.objects.create(
                    recipient=post_obj.author,
                    sender=request.user,
                    message=f'{request.user.username} ha comentado en tu post "{post_obj.title}".',
                    link=post_obj.get_absolute_url() + f'#comment-{comment.id}'
                )

            return redirect(post_obj.get_absolute_url())
        else:
            return self.get(request, *args, **kwargs)


class PostCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def test_func(self):
        return self.request.user.profile.can_post

    def form_valid(self, form):
        from .services import TagManagerService
        
        form.instance.author = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        
        # Procesar tags con el sistema inteligente
        tags_input = self.request.POST.get('tags', '')
        if tags_input:
            # Dividir por comas y limpiar
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Usar el servicio de tags inteligente
            tag_manager = TagManagerService()
            processed_tags = tag_manager.process_post_tags(self.object, tag_names, self.request.user)
            
            # Asignar tags al post
            self.object.tags.set(processed_tags)
        
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def form_valid(self, form):
        from .services import TagManagerService
        
        self.object = form.save(commit=False)
        self.object.save()
        
        # Procesar tags con el sistema inteligente
        tags_input = self.request.POST.get('tags', '')
        if tags_input:
            # Dividir por comas y limpiar
            tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
            
            # Usar el servicio de tags inteligente
            tag_manager = TagManagerService()
            processed_tags = tag_manager.process_post_tags(self.object, tag_names, self.request.user)
            
            # Asignar tags al post
            self.object.tags.set(processed_tags)
        else:
            # Si no hay tags, limpiar
            self.object.tags.clear()
        
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = "posts/post_confirm_delete.html"

    def get_success_url(self):
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy("posts:post_list")

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


@login_required
def dashboard_view(request):
    user = request.user
    user_posts = Post.objects.filter(author=user)

    total_posts = user_posts.count()
    total_views = user_posts.aggregate(total=Sum("views"))["total"] or 0
    total_likes = user_posts.aggregate(total=Count("likes"))["total"] or 0
    total_comments = Comment.objects.filter(post__in=user_posts).count()

    stats = {
        "total_posts": total_posts,
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
    }

    top_posts = user_posts.order_by("-views")[:3]


    today = date.today()
    labels = [(today - timedelta(days=i)).strftime("%d %b") for i in range(29, -1, -1)]
    chart_data_points = [
        5,
        10,
        8,
        15,
        12,
        18,
        20,
        25,
        22,
        30,
        35,
        40,
        38,
        45,
        50,
        48,
        55,
        60,
        58,
        65,
        70,
        68,
        75,
        80,
        78,
        85,
        90,
        88,
        95,
        100,
    ]

    chart_data = {
        "labels": labels,
        "data": chart_data_points,
    }

    unread_notifications_count = Notification.objects.filter(recipient=user, is_read=False).count()

    context = {
        "user_posts": user_posts.order_by("-created_at"),
        "stats": stats,
        "top_posts": top_posts,
        "notification_count": unread_notifications_count, 
        "chart_data": json.dumps(chart_data),
    }
    return render(request, "posts/dashboard.html", context)



@ajax_required
@csrf_exempt
def like_post(request, username, slug):
    """Handle post likes with proper authentication and error handling."""
    
    try:
        # Get post with proper error handling
        post = get_object_or_404(Post, author__username=username, slug=slug, status='published')
        
        # Note: Allowing users to like their own posts for flexibility
        
        # Check if user already liked the post (more efficient)
        user_liked = post.likes.filter(id=request.user.id).exists()
        
        if user_liked:
            post.likes.remove(request.user)
            liked = False
            message = 'Like removido correctamente'
        else:
            post.likes.add(request.user)
            liked = True
            message = 'Like agregado correctamente'
        
        # Log the action for analytics
        logger.info(f"User {request.user.username} {'liked' if liked else 'unliked'} post {post.slug}")
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': post.likes.count(),
            'message': message
        })
        
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Post no encontrado'
        }, status=404)
    except Exception as e:
        # Log error properly
        logger.error(f"Error in like_post for user {request.user.username}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@ajax_required
@csrf_exempt
def like_comment(request, pk):
    """Handle comment likes with proper authentication and error handling."""
    
    try:
        comment = get_object_or_404(Comment, pk=pk, active=True)
        
        # Check if user already liked the comment (more efficient)
        user_liked = comment.likes.filter(id=request.user.id).exists()
        
        if user_liked:
            comment.likes.remove(request.user)
            liked = False
            message = 'Like removido del comentario'
        else:
            comment.likes.add(request.user)
            liked = True
            message = 'Like agregado al comentario'
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': comment.likes.count(),
            'message': message
        })
        
    except Comment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Comentario no encontrado'
        }, status=404)
    except Exception as e:
        # Log error properly
        logger.error(f"Error in like_comment: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@ajax_required
@csrf_exempt
def favorite_post(request, username, slug):
    """Handle post favorites with consistent URL pattern."""
    
    try:
        post = get_object_or_404(Post, author__username=username, slug=slug, status='published')
        
        # Check if user already favorited the post
        user_favorited = post.favorites.filter(id=request.user.id).exists()
        
        if user_favorited:
            post.favorites.remove(request.user)
            favorited = False
            message = 'Removido de favoritos'
        else:
            post.favorites.add(request.user)
            favorited = True
            message = 'Agregado a favoritos'
        
        return JsonResponse({
            'success': True,
            'favorited': favorited,
            'favorites_count': post.favorites.count(),
            'message': message
        })
        
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Post no encontrado'
        }, status=404)
    except Exception as e:
        # Log error properly
        logger.error(f"Error in favorite_post: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Error interno del servidor'
        }, status=500)


@login_required
def favorite_list(request):
    favorite_posts = request.user.favorite_posts.all()
    return render(
        request, "posts/favorite_list.html", {"favorite_posts": favorite_posts}
    )


class SearchResultsView(ListView):
    model = Post
    template_name = "posts/search_results.html"
    paginate_by = 12  # Agregar paginación a búsquedas
    
    @method_decorator(search_rate_limit(rate='30/m'))
    def get(self, request, *args, **kwargs):
        # Registrar búsqueda
        query = request.GET.get('q', '')
        ip = get_client_ip(request)
        
        if query:
            logger.info(
                f"Búsqueda realizada: query='{query}', ip={ip}",
                extra={
                    'query': query,
                    'ip': ip,
                    'user_id': getattr(request.user, 'id', None),
                }
            )
        
        return super().get(request, *args, **kwargs)
    context_object_name = "posts"

    def get_queryset(self):
        query = self.request.GET.get("q")
        if query:
            return Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query),
                status="published"
            ).select_related('author', 'author__profile').prefetch_related('tags', 'likes', 'comments').distinct().order_by('-created_at')
        return Post.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class CommentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = "posts/comment_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("posts:post_detail", kwargs={"username": self.object.post.author.username, "slug": self.object.post.slug})

    def test_func(self):
        comment = self.get_object()
        return (
            self.request.user == comment.author
            or self.request.user == comment.post.author
        )

class PostArchiveView(ArchiveIndexView):
    model = Post
    date_field = "created_at"
    template_name = "posts/post_archive.html"
    context_object_name = "archives"
    allow_future = False

    def get_queryset(self):
        return Post.objects.filter(status="published").order_by("-created_at")

def _check_post_permission(user):
    """Helper function to check if user has posting permissions"""
    return user.is_authenticated and user.profile.can_post

def _create_ai_post(title, content, tags_list, author, cover_image_url=None):
    """Helper function to create AI-generated post"""
    # Handle tags properly
    if isinstance(tags_list, list):
        tags_string = ', '.join(tags_list)
    else:
        tags_string = str(tags_list)
    
    # Create the post
    post = Post.objects.create(
        title=title,
        content=content,
        status='draft',
        author=author
    )
    
    # Handle cover image if provided
    if cover_image_url:
        try:
            from django.core.files.base import ContentFile
            from django.core.files.storage import default_storage
            import requests
            import os
            from urllib.parse import urlparse
            
            # If it's a local URL, convert to file path
            if cover_image_url.startswith('/media/'):
                # It's already saved locally, just update the field
                # Remove /media/ prefix to get the relative path
                relative_path = cover_image_url.replace('/media/', '')
                post.header_image = relative_path
                post.save()
            else:
                # It's an external URL, download and save
                response = requests.get(cover_image_url, timeout=30)
                response.raise_for_status()
                
                # Generate filename
                parsed_url = urlparse(cover_image_url)
                filename = f"ai_cover_{post.id}_{os.path.basename(parsed_url.path)}"
                if not filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    filename += '.jpg'
                
                # Save the image
                image_content = ContentFile(response.content)
                saved_path = default_storage.save(f'post_images/{filename}', image_content)
                
                # Update post with image
                post.header_image = saved_path
                post.save()
                
        except Exception as e:
            # Log error but don't fail the post creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error saving cover image for post {post.id}: {e}")
    
    # Add tags if they exist
    if tags_string.strip():
        # Split tags and add them properly
        tag_names = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        for tag_name in tag_names:
            post.tags.add(tag_name)
    
    return post

def _generate_ai_content(url, rewrite_prompt, tag_prompt, form_data=None):
    """Helper function to generate AI content from URL"""
    from .prompt_manager import PromptManager
    
    # Extract content from URL
    url_data = extract_content_from_url(url)
    
    if not url_data or not url_data.get('content'):
        return None, 'No se pudo extraer contenido de la URL proporcionada.'
    
    try:
        # Check if using advanced generation
        prompt_type = form_data.get('prompt_type', 'simple') if form_data else 'simple'
        
        # Debug: mostrar datos del formulario
        print(f"🔍 Datos del formulario recibidos:")
        if form_data:
            for key, value in form_data.items():
                print(f"   {key}: {value}")
        
        # Obtener prompts desde la base de datos si están especificados
        if form_data:
            content_template_id = form_data.get('content_prompt_template')
            tag_template_id = form_data.get('tag_prompt_template')
            
            # Usar prompt personalizado para contenido si está especificado
            if content_template_id:
                try:
                    content_template = PromptManager.get_prompt_by_id(int(content_template_id))
                    rewrite_prompt = content_template.template
                    print(f"✅ Usando prompt personalizado para contenido: {content_template.name}")
                except (ValueError, Exception) as e:
                    # Usar el prompt por defecto si hay error
                    rewrite_prompt = PromptManager.get_default_prompt('content')
                    print(f"⚠️ Error con prompt personalizado, usando por defecto: {e}")
            
            # Usar prompt personalizado para tags si está especificado
            if tag_template_id:
                try:
                    tag_template = PromptManager.get_prompt_by_id(int(tag_template_id))
                    tag_prompt = tag_template.template
                    print(f"✅ Usando prompt personalizado para tags: {tag_template.name}")
                except (ValueError, Exception) as e:
                    # Usar el prompt por defecto si hay error
                    tag_prompt = PromptManager.get_default_prompt('tags')
                    print(f"⚠️ Error con prompt personalizado, usando por defecto: {e}")
        
        if prompt_type == 'complete' and form_data:
            # Use advanced function with new image generation options
            extract_images = form_data.get('extract_images', False)
            max_images = form_data.get('max_images', 5)
            
            # New image generation parameters
            generate_cover = form_data.get('generate_cover_image', False)
            image_style = form_data.get('cover_image_style', 'professional')
            title = form_data.get('title')
            
            print(f"🎨 Parámetros de imagen extraídos:")
            print(f"   - generate_cover: {generate_cover}")
            print(f"   - image_style: {image_style}")
            print(f"   - title: {title}")
            
            result = generate_complete_post(
                url=url,
                rewrite_prompt=rewrite_prompt,
                extract_images=extract_images,
                max_images=max_images,
                title=title,
                generate_cover=generate_cover,
                image_style=image_style
            )
            
            if result['success']:
                return {
                    'title': result['title'],
                    'content': result['content'],
                    'tags': result['tags'],
                    'cover_image_url': result.get('cover_image_url')
                }, None
            else:
                return None, f'Error al generar el post: {result.get("error", "Error desconocido")}'
        
        else:
            # Traditional method
            content_text = url_data['content'] if isinstance(url_data, dict) else url_data
            
            # Generate title and content
            title, content = rewrite_content_with_ai(content_text, rewrite_prompt)
            
            # Generate tags separately
            tags_list = generate_tags_with_ai(content_text, tag_prompt)
            
            return {
                'title': title,
                'content': content,
                'tags': tags_list,
                'cover_image_url': None
            }, None
            
    except Exception as e:
        return None, f'Error al procesar el contenido: {str(e)}'

@login_required
def ai_post_generator_view(request):
    """
    Vista para generar posts con IA - Refactorizada y optimizada
    """
    if not _check_post_permission(request.user):
        messages.error(request, 'No tienes permisos para crear posts. Solicita permisos al administrador.')
        return redirect('posts:post_list')
    
    if request.method == 'POST':
        form = AiPostGeneratorForm(request.POST)
        if form.is_valid():
            try:
                url = form.cleaned_data['url']
                rewrite_prompt = form.cleaned_data['rewrite_prompt']
                tag_prompt = form.cleaned_data['tag_prompt']
                
                # Generate AI content using helper function
                result, error = _generate_ai_content(url, rewrite_prompt, tag_prompt, form.cleaned_data)
                
                if error:
                    messages.error(request, error)
                    return render(request, 'posts/ai_generator.html', {'form': form})
                
                # Create post using helper function
                post = _create_ai_post(
                    result['title'],
                    result['content'],
                    result['tags'],
                    request.user,
                    result.get('cover_image_url')
                )
                
                messages.success(request, f'Post "{result["title"]}" generado exitosamente!')
                return redirect('posts:post_detail', username=request.user.username, slug=post.slug)
                
            except Exception as e:
                messages.error(request, f'Ocurrió un error: {str(e)}')
                # Log error properly
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in AI post generation: {e}", exc_info=True)
                return render(request, 'posts/ai_generator.html', {'form': form})
    else:
        form = AiPostGeneratorForm()
    
    return render(request, 'posts/ai_generator.html', {'form': form})

@login_required
def ai_post_generator_simple_view(request):
    """
    Vista simplificada usando funciones helper refactorizadas
    """
    if not _check_post_permission(request.user):
        messages.error(request, 'No tienes permisos para crear posts. Solicita permisos al administrador.')
        return redirect('posts:post_list')
    
    if request.method == 'POST':
        form = AiPostGeneratorForm(request.POST)
        if form.is_valid():
            try:
                url = form.cleaned_data['url']
                rewrite_prompt = form.cleaned_data['rewrite_prompt']
                tag_prompt = form.cleaned_data['tag_prompt']
                
                # Generate AI content using helper function (simple mode)
                result, error = _generate_ai_content(url, rewrite_prompt, tag_prompt)
                
                if error:
                    messages.error(request, error)
                    return render(request, 'posts/ai_generator.html', {'form': form})
                
                # Create post using helper function
                post = _create_ai_post(
                    result['title'],
                    result['content'],
                    result['tags'],
                    request.user,
                    result.get('cover_image_url')
                )
                
                messages.success(request, 'Post generado exitosamente!')
                return redirect('posts:post_detail', username=request.user.username, slug=post.slug)
                
            except ValueError as e:
                if "too many values to unpack" in str(e):
                    messages.error(request, 'Error en la configuración de la IA. Por favor contacta al administrador.')
                else:
                    messages.error(request, f'Error: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
                # Log error properly
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error in simple AI post generation: {e}", exc_info=True)
    else:
        form = AiPostGeneratorForm()
    
    return render(request, 'posts/ai_generator.html', {'form': form})
@login_required
def ai_post_generator_view(request):
    """Vista para el generador de posts con IA."""
    from .forms import AiPostGeneratorForm
    from .ai_generator import generate_complete_post
    
    if not _check_post_permission(request.user):
        messages.error(request, 'No tienes permisos para crear posts.')
        return redirect('posts:post_list')
    
    if request.method == 'POST':
        form = AiPostGeneratorForm(request.POST)
        if form.is_valid():
            try:
                # Extraer datos del formulario
                url = form.cleaned_data.get('url')
                title = form.cleaned_data.get('title')
                rewrite_prompt = form.cleaned_data.get('rewrite_prompt')
                tag_prompt = form.cleaned_data.get('tag_prompt')
                extract_images = form.cleaned_data.get('extract_images', False)
                max_images = form.cleaned_data.get('max_images', 5)
                # Siempre priorizar imágenes grandes y asignar automáticamente la primera como portada
                prioritize_large_images = True
                
                # Generar el post
                result = generate_complete_post(
                    url=url,
                    title=title,
                    rewrite_prompt=rewrite_prompt,
                    tag_prompt=tag_prompt,
                    extract_images=extract_images,
                    max_images=max_images,
                    prioritize_large_images=prioritize_large_images
                )
                
                if result.get('success'):
                    # Crear el post
                    post = Post.objects.create(
                        title=result['title'],
                        content=result['content'],
                        author=request.user,
                        status='draft',
                        reading_time=result.get('reading_time', 1)
                    )
                    
                    # Agregar tags
                    if result.get('tags'):
                        for tag_name in result['tags']:
                            post.tags.add(tag_name.strip())
                    
                    # Asignar automáticamente la primera imagen extraída como portada
                    if extract_images and result.get('suggested_cover_image'):
                        try:
                            suggested_image = result['suggested_cover_image']
                            relative_path = suggested_image['path']
                            post.header_image = relative_path
                            post.save()
                            logger.info(f"✅ Imagen de portada asignada automáticamente: {relative_path}")
                            messages.success(request, f'Se asignó automáticamente la primera imagen extraída como portada: {suggested_image["filename"]}')
                        except Exception as e:
                            logger.error(f"❌ Error asignando imagen de portada: {e}")
                            messages.warning(request, 'No se pudo asignar la imagen de portada automáticamente.')
                    
                    # Informar sobre imágenes disponibles
                    available_images = result.get('available_cover_images', [])
                    if available_images:
                        messages.info(request, f'Se extrajeron {len(available_images)} imágenes. Puedes cambiar la portada editando el post.')
                    elif extract_images:
                        messages.warning(request, 'No se pudieron extraer imágenes del contenido.')
                    
                    if post:
                        messages.success(request, f'Post "{post.title}" generado exitosamente.')
                        return redirect('posts:post_detail', username=post.author.username, slug=post.slug)
                    else:
                        messages.error(request, 'Error al crear el post en la base de datos.')
                else:
                    error_msg = result.get('error', 'Error desconocido en la generación')
                    messages.error(request, f'Error generando el post: {error_msg}')
                    
            except Exception as e:
                logger.error(f"Error en ai_post_generator_view: {e}")
                messages.error(request, f'Error inesperado: {str(e)}')
    else:
        form = AiPostGeneratorForm()
    
    return render(request, 'admin/posts/post/ai_generator.html', {
        'form': form,
        'title': 'Generador de Posts con IA'
    })

@login_required
def ai_post_generator_simple_view(request):
    """Vista simplificada para el generador de posts con IA."""
    return ai_post_generator_view(request)
@login_required
def api_existing_images(request):
    """API endpoint para obtener imágenes existentes."""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        images = []
        
        # Folders to search for images
        image_folders = [
            'ai_posts/covers/',
            'post_images/',
            'uploads/',
            'images/',
        ]
        
        for folder in image_folders:
            try:
                if default_storage.exists(folder):
                    # List files in folder
                    _, files = default_storage.listdir(folder)
                    
                    for file in files:
                        if is_image_file(file):
                            file_path = os.path.join(folder, file).replace('\\', '/')
                            images.append({
                                'path': file_path,
                                'url': default_storage.url(file_path),
                                'name': file,
                                'folder': folder
                            })
            except Exception:
                continue
        
        # Sort by name (newest first)
        images = sorted(images, key=lambda x: x['name'], reverse=True)[:30]
        
        return JsonResponse({'images': images})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def is_image_file(filename):
    """Check if file is an image."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    return any(filename.lower().endswith(ext) for ext in image_extensions)