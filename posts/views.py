from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django_ckeditor_5 import views as ckeditor_views
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.views.generic.dates import ArchiveIndexView
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import Post, Comment
from .forms import CommentForm, PostForm, AiPostGeneratorForm
from taggit.models import Tag
from accounts.models import Notification
from django.contrib import messages
from .ai_generator import extract_content_from_url, rewrite_content_with_ai, generate_tags_with_ai, generate_complete_post

from django.db.models import Q, Sum, Count
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
    Vista para manejar la subida de imágenes desde CKEditor.
    """
    if request.method == 'POST' and request.FILES.get('upload'):
        uploaded_file = request.FILES['upload']
        
        # Validación básica del archivo
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in allowed_extensions:
            return JsonResponse({'error': {'message': 'Tipo de archivo no permitido.'}}, status=400)
            
        if uploaded_file.size > 8 * 1024 * 1024: # Límite de 8MB
            return JsonResponse({'error': {'message': 'El archivo es demasiado grande (máx 8MB).'}}, status=400)

        # Guardar el archivo y obtener la URL
        try:
            file_path = default_storage.save(f'uploads/posts_content/{uploaded_file.name}', uploaded_file)
            file_url = default_storage.url(file_path)
            return JsonResponse({'url': file_url})
        except Exception as e:
            return JsonResponse({'error': {'message': f'Error al guardar el archivo: {e}'}}, status=500)
    
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
        return Post.objects.filter(status="published").order_by("-created_at")

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


class PostListByTagView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "object_list"
    paginate_by = 6

    def get_queryset(self):
        tag_slug = self.kwargs.get("tag_slug")
        tag = get_object_or_404(Tag, slug=tag_slug)
        return Post.objects.filter(tags__in=[tag], status="published").order_by("-created_at")

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
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    lookup_field = "slug"



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
        post = get_object_or_404(Post, author__username=username, slug=slug)
        post.views += 1
        post.save(update_fields=["views"])
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
def like_post(request, username, slug):
    """Handle post likes with proper authentication."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    post = get_object_or_404(Post, author__username=username, slug=slug)
    
    try:
        if request.user in post.likes.all():
            post.likes.remove(request.user)
            liked = False
        else:
            post.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': post.likes.count(),
            'message': 'Like actualizado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@csrf_exempt
def like_comment(request, pk):
    """Handle comment likes with proper authentication."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    comment = get_object_or_404(Comment, pk=pk)
    
    try:
        if request.user in comment.likes.all():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            liked = True
        
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likes_count': comment.likes.count(),
            'message': 'Like actualizado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def favorite_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user in post.favorites.all():
        post.favorites.remove(request.user)
        favorited = False
    else:
        post.favorites.add(request.user)
        favorited = True
    return JsonResponse({'favorited': favorited})


@login_required
def favorite_list(request):
    favorite_posts = request.user.favorite_posts.all()
    return render(
        request, "posts/favorite_list.html", {"favorite_posts": favorite_posts}
    )


class SearchResultsView(ListView):
    model = Post
    template_name = "posts/search_results.html"
    context_object_name = "posts"

    def get_queryset(self):
        query = self.request.GET.get("q")
        if query:
            return Post.objects.filter(
                Q(title__icontains=query) | Q(content__icontains=query)
            ).distinct()
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

def ai_post_generator_view(request):
    """
    Vista para generar posts con IA - Compatible con tu código existente
    """
    if request.method == 'POST':
        form = AiPostGeneratorForm(request.POST)
        if form.is_valid():
            try:
                url = form.cleaned_data['url']
                rewrite_prompt = form.cleaned_data['rewrite_prompt']
                tag_prompt = form.cleaned_data['tag_prompt']
                
                # Extraer contenido de la URL
                url_data = extract_content_from_url(url)
                
                if not url_data or not url_data.get('content'):
                    messages.error(request, 'No se pudo extraer contenido de la URL proporcionada.')
                    return render(request, 'posts/ai_generator.html', {'form': form})
                
                # Verificar si usa el prompt completo o simple
                prompt_type = form.cleaned_data.get('prompt_type', 'complete')
                
                if prompt_type == 'complete' and hasattr(form.cleaned_data, 'extract_images'):
                    # Usar la función avanzada si está disponible
                    extract_images = form.cleaned_data.get('extract_images', False)
                    max_images = form.cleaned_data.get('max_images', 5)
                    
                    result = generate_complete_post(
                        url=url,
                        rewrite_prompt=rewrite_prompt,
                        extract_images=extract_images,
                        max_images=max_images
                    )
                    
                    if result['success']:
                        title = result['title']
                        content = result['content']
                        tags_list = result['tags']
                    else:
                        messages.error(request, f'Error al generar el post: {result.get("error", "Error desconocido")}')
                        return render(request, 'posts/ai_generator.html', {'form': form})
                
                else:
                    # Método tradicional - compatible con código existente
                    content_text = url_data['content'] if isinstance(url_data, dict) else url_data
                    
                    # Generar título y contenido
                    title, content = rewrite_content_with_ai(content_text, rewrite_prompt)
                    
                    # Generar tags por separado
                    tags_list = generate_tags_with_ai(content_text, tag_prompt)
                
                # Crear el post
                post = Post.objects.create(
                    title=title,
                    content=content,
                    tags=', '.join(tags_list) if isinstance(tags_list, list) else tags_list,
                    status='draft',  # Crear como borrador inicialmente
                    author=request.user  # Si tienes campo author
                )
                
                messages.success(request, f'Post "{title}" generado exitosamente!')
                return redirect('post_detail', pk=post.pk)  # Ajusta según tu URL
                
            except Exception as e:
                messages.error(request, f'Ocurrió un error: {str(e)}')
                print(f"Error detallado: {e}")  # Para debugging
                return render(request, 'posts/ai_generator.html', {'form': form})
    else:
        form = AiPostGeneratorForm()
    
    return render(request, 'posts/ai_generator.html', {'form': form})

def ai_post_generator_simple_view(request):
    """
    Vista simplificada que garantiza compatibilidad con código existente
    """
    if request.method == 'POST':
        form = AiPostGeneratorForm(request.POST)
        if form.is_valid():
            try:
                url = form.cleaned_data['url']
                rewrite_prompt = form.cleaned_data['rewrite_prompt']
                tag_prompt = form.cleaned_data['tag_prompt']
                
                # Paso 1: Extraer contenido
                content = extract_content_from_url(url)
                
                if not content:
                    messages.error(request, 'No se pudo extraer contenido de la URL.')
                    return render(request, 'posts/ai_generator.html', {'form': form})
                
                # Manejar tanto dict como string
                content_text = content.get('content', content) if isinstance(content, dict) else content
                
                # Paso 2: Reescribir contenido (función original que devuelve tupla)
                title, rewritten_content = rewrite_content_with_ai(content_text, rewrite_prompt)
                
                # Paso 3: Generar tags
                tags = generate_tags_with_ai(content_text, tag_prompt)
                tags_string = ', '.join(tags) if isinstance(tags, list) else str(tags)
                
                # Paso 4: Crear post
                post = Post.objects.create(
                    title=title,
                    content=rewritten_content,
                    tags=tags_string,
                    status='draft'
                )
                
                messages.success(request, 'Post generado exitosamente!')
                return redirect('post_detail', pk=post.pk)
                
            except ValueError as e:
                if "too many values to unpack" in str(e):
                    messages.error(request, 'Error en la configuración de la IA. Por favor contacta al administrador.')
                else:
                    messages.error(request, f'Error: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error inesperado: {str(e)}')
                print(f"Error completo: {e}")  # Para debugging
    else:
        form = AiPostGeneratorForm()
    
    return render(request, 'posts/ai_generator.html', {'form': form})