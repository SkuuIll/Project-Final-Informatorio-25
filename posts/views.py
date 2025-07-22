from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
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
@write_rate_limit(rate='20/minute')
def upload_image_view(request):
    """
    Vista para manejar la subida de imágenes desde CKEditor con seguridad avanzada.
    """
    if request.method == 'POST' and request.FILES.get('upload'):
        uploaded_file = request.FILES['upload']
        
        # Usar el validador seguro
        from blog.file_utils import SecureFileValidator, secure_save_uploaded_file
        
        # Registrar intento de subida
        ip = get_client_ip(request)
        logger.info(
            f"Intento de subida de imagen: {uploaded_file.name}, tamaño={uploaded_file.size}, ip={ip}",
            extra={
                'user_id': request.user.id,
                'ip': ip,
                'filename': uploaded_file.name,
                'filesize': uploaded_file.size,
            }
        )
        
        # Guardar archivo de forma segura
        success, result = secure_save_uploaded_file(
            uploaded_file,
            'uploads/posts_content',
            validate_func=SecureFileValidator.validate_image,
            optimize=True
        )
        
        if success:
            file_url = default_storage.url(result)
            return JsonResponse({'url': file_url})
        else:
            return JsonResponse({'error': {'message': result}}, status=400)
    
    return JsonResponse({'error': {'message': 'Petición no válida.'}}, status=400)


@csrf_exempt
@login_required
def custom_upload_file(request):
    return ckeditor_views.image_upload(request)
   

class PostListView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "object_list"
    paginate_by = 6

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
    paginate_by = 6

    def get_queryset(self):
        tag_slug = self.kwargs.get("tag_slug")
        # Usar el manager optimizado para posts con tag específico
        return Post.optimized.with_tag(tag_slug).with_stats().order_by("-created_at")

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



    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "object_list"
    # paginate_by = 12

    def get_queryset(self):
        queryset = Post.objects.filter(status="published")
        sort_by = self.request.GET.get('sort_by', '-created_at')

        if sort_by == 'likes':
            queryset = queryset.annotate(num_likes=Count('likes')).order_by('-is_sticky', '-num_likes', '-created_at')
        elif sort_by == 'views':
            queryset = queryset.order_by('-is_sticky', '-views', '-created_at')
        elif sort_by == 'comments':
            queryset = queryset.annotate(num_comments=Count('comments')).order_by('-is_sticky', '-num_comments', '-created_at')
        else:
            queryset = queryset.order_by('-is_sticky', sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_tags'] = Tag.objects.annotate(num_posts=Count('post')).order_by('-num_posts')[:4]
        context['sort_by'] = self.request.GET.get('sort_by', '-created_at')
        one_day_ago = timezone.now() - timedelta(days=1)
        latest_posts = Post.objects.filter(status="published", created_at__gte=one_day_ago).order_by('-created_at')[:5]
        context['latest_post_ids'] = [post.id for post in latest_posts]
        return context


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
        form.instance.author = self.request.user
        self.object = form.save(commit=False)
        self.object.save()
        tags = self.request.POST.getlist('tags')
        tag_objects = []
        for tag_name in tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag_objects.append(tag)
        self.object.tags.set(tag_objects)
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        tags = self.request.POST.getlist('tags')
        tag_objects = []
        for tag_name in tags:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tag_objects.append(tag)
        self.object.tags.set(tag_objects)
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



@login_required
@csrf_exempt
@write_rate_limit(rate='30/minute')
def like_post(request, username, slug):
    """Handle post likes with proper authentication and error handling."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    # Validate user is authenticated (extra check)
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Debes iniciar sesión para dar like'
        }, status=401)
    
    try:
        # Get post with proper error handling
        post = get_object_or_404(Post, author__username=username, slug=slug, status='published')
        
        # Prevent users from liking their own posts (optional business rule)
        if post.author == request.user:
            return JsonResponse({
                'success': False,
                'error': 'No puedes dar like a tu propio post'
            }, status=400)
        
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


@login_required
@csrf_exempt
@write_rate_limit(rate='30/minute')
def like_comment(request, pk):
    """Handle comment likes with proper authentication and error handling."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    # Validate user is authenticated (extra check)
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Debes iniciar sesión para dar like'
        }, status=401)
    
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


@login_required
@csrf_exempt
@write_rate_limit(rate='30/minute')
def favorite_post(request, username, slug):
    """Handle post favorites with consistent URL pattern."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    # Validate user is authenticated (extra check)
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Debes iniciar sesión para agregar favoritos'
        }, status=401)
    
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

def _create_ai_post(title, content, tags_list, author):
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
    
    # Add tags if they exist
    if tags_string.strip():
        # Split tags and add them properly
        tag_names = [tag.strip() for tag in tags_string.split(',') if tag.strip()]
        for tag_name in tag_names:
            post.tags.add(tag_name)
    
    return post

def _generate_ai_content(url, rewrite_prompt, tag_prompt, form_data=None):
    """Helper function to generate AI content from URL"""
    # Extract content from URL
    url_data = extract_content_from_url(url)
    
    if not url_data or not url_data.get('content'):
        return None, 'No se pudo extraer contenido de la URL proporcionada.'
    
    try:
        # Check if using advanced generation
        prompt_type = form_data.get('prompt_type', 'simple') if form_data else 'simple'
        
        if prompt_type == 'complete' and form_data and hasattr(form_data, 'extract_images'):
            # Use advanced function if available
            extract_images = form_data.get('extract_images', False)
            max_images = form_data.get('max_images', 5)
            
            result = generate_complete_post(
                url=url,
                rewrite_prompt=rewrite_prompt,
                extract_images=extract_images,
                max_images=max_images
            )
            
            if result['success']:
                return {
                    'title': result['title'],
                    'content': result['content'],
                    'tags': result['tags']
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
                'tags': tags_list
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
                    request.user
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
                    request.user
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