from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.views.generic.dates import ArchiveIndexView
from .models import Post, Comment
from .forms import CommentForm, PostForm
from taggit.models import Tag
from accounts.models import Notification

from django.db.models import Q, Sum, Count
from rest_framework import viewsets
from .serializers import PostSerializer

# Imports for dashboard
from datetime import date, timedelta
import json
   

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
        context['all_tags'] = Tag.objects.all()
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


class PostListView(ListView):
    model = Post
    template_name = "posts/post_list.html"
    context_object_name = "object_list"
    ordering = ["-created_at"]
    paginate_by = 6

    def get_queryset(self):
        return Post.objects.filter(status="published")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_tags'] = Tag.objects.all()
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"

    def get_object(self, queryset=None):
        post = super().get_object(queryset)
        post.views += 1
        post.save(update_fields=["views"])
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        context["comment_form"] = CommentForm()

        # Obtener la URL absoluta del post para compartir en redes sociales
        context['post_url'] = self.request.build_absolute_uri(post.get_absolute_url())
        
        if post.header_image:
            context['og_image_url'] = self.request.build_absolute_uri(post.header_image.url)
        else:
            # Opcional: proveer una imagen por defecto si no hay header_image
            context['og_image_url'] = self.request.build_absolute_uri('/static/social_banner.png')


        post_tags_ids = post.tags.values_list("id", flat=True)
        similar_posts = Post.objects.filter(tags__in=post_tags_ids).exclude(id=post.id)
        context["similar_posts"] = similar_posts.distinct().order_by("-created_at")[:4]

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

            # Crear notificación si el autor del comentario no es el autor del post
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
        return super().form_valid(form)


class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author


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

    # Calcular estadísticas generales
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

    # Obtener los posts más populares del usuario
    top_posts = user_posts.order_by("-views")[:3]

    # --- Datos para el gráfico ---
    # NOTA: Esta es una simulación. Para un gráfico real, necesitarías un modelo
    # que registre cada vista con una marca de tiempo.
    today = date.today()
    labels = [(today - timedelta(days=i)).strftime("%d %b") for i in range(29, -1, -1)]
    # Generamos datos de ejemplo. Reemplaza esto con tu lógica real.
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

    # Obtener el recuento real de notificaciones no leídas
    unread_notifications_count = Notification.objects.filter(recipient=user, is_read=False).count()

    context = {
        "user_posts": user_posts.order_by("-created_at"),
        "stats": stats,
        "top_posts": top_posts,
        "notification_count": unread_notifications_count,  # Usar el recuento dinámico
        "chart_data": json.dumps(chart_data),
    }
    return render(request, "posts/dashboard.html", context)


@login_required
def like_post(request, slug):
    post = get_object_or_404(Post, slug=slug)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    return JsonResponse({'liked': liked, 'likes_count': post.likes.count()})


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
        return reverse_lazy("posts:post_detail", kwargs={"slug": self.object.post.slug})

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
