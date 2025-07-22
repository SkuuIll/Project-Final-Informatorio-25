from django.db import models
from django.db.models import Count, F, Q


class PostQuerySet(models.QuerySet):
    """
    Custom QuerySet for Post model with chainable methods.
    """
    
    def published(self):
        """Retorna solo posts publicados."""
        return self.filter(status="published")
    
    def with_author(self):
        """Incluye el autor y su perfil en una sola consulta."""
        return self.select_related('author', 'author__profile')
    
    def with_relations(self):
        """Carga todas las relaciones comunes en una sola consulta."""
        return self.select_related(
            'author', 
            'author__profile'
        ).prefetch_related(
            'tags',
            'comments__author__profile',
            'likes',
            'favorites'
        )
    
    def with_stats(self):
        """Añade estadísticas completas como anotaciones."""
        return self.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            favorites_count=Count('favorites', distinct=True)
        )
    
    def with_counts(self):
        """Añade conteos de likes, comentarios, etc. como anotaciones."""
        return self.annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            favorites_count=Count('favorites', distinct=True)
        )
    
    def sticky_first(self):
        """Retorna posts con los destacados primero."""
        return self.order_by('-is_sticky', '-created_at')
    
    def by_tag(self, tag_slug):
        """Filtra posts por tag slug."""
        return self.published().filter(tags__slug=tag_slug)
    
    def search(self, query):
        """Búsqueda optimizada en posts."""
        return self.published().filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) |
            Q(author__username__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()


class CommentQuerySet(models.QuerySet):
    """
    Custom QuerySet for Comment model with chainable methods.
    """
    
    def active(self):
        """Retorna solo comentarios activos."""
        return self.filter(active=True)
    
    def with_author(self):
        """Incluye el autor en una sola consulta."""
        return self.select_related('author', 'author__profile')
    
    def with_post_info(self):
        """Include post information with comments."""
        return self.select_related(
            'post', 
            'author', 
            'author__profile',
            'post__author',
            'post__author__profile'
        )
    
    def with_likes(self):
        """Añade conteo de likes como anotación."""
        return self.annotate(likes_count=Count('likes', distinct=True))


class AIModelManager(models.Manager):
    """
    Manager optimizado para el modelo AIModel.
    """
    
    def active(self):
        """Retorna el modelo de IA activo."""
        return self.filter(is_active=True).first()
    
    def all_with_usage_stats(self):
        """Retorna todos los modelos con estadísticas de uso."""
        # Esta es una implementación de ejemplo. En un caso real,
        # necesitaríamos una tabla de estadísticas de uso.
        return self.all()


class PostManager(models.Manager):
    """
    Manager optimizado para el modelo Post con métodos que utilizan
    select_related y prefetch_related para evitar problemas N+1.
    """
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return PostQuerySet(self.model, using=self._db)
    
    def published(self):
        """Retorna solo posts publicados."""
        return self.get_queryset().published()
    
    def with_author(self):
        """Incluye el autor y su perfil en una sola consulta."""
        return self.get_queryset().with_author()
    
    def with_relations(self):
        """Carga todas las relaciones comunes en una sola consulta."""
        return self.get_queryset().with_relations()
    
    def with_stats(self):
        """Añade estadísticas completas como anotaciones."""
        return self.get_queryset().with_stats()
    
    def with_counts(self):
        """Añade conteos de likes, comentarios, etc. como anotaciones."""
        return self.get_queryset().with_counts()
    
    def sticky_first(self):
        """Retorna posts con los destacados primero."""
        return self.get_queryset().sticky_first()
    
    def published_with_relations(self):
        """Combina published() y with_relations()."""
        return self.get_queryset().published().with_relations()
    
    def with_tag(self, tag_slug):
        """Filtra posts por tag slug y añade relaciones."""
        return self.get_queryset().published().filter(tags__slug=tag_slug).with_relations()
    
    def popular(self):
        """Retorna posts ordenados por popularidad (vistas + likes)."""
        return self.get_queryset().with_stats().annotate(
            popularity=F('views') + Count('likes')
        ).order_by('-popularity')
    
    def by_tag(self, tag_slug):
        """Filtra posts por tag slug."""
        return self.get_queryset().by_tag(tag_slug)
    
    def search(self, query):
        """Búsqueda optimizada en posts."""
        return self.get_queryset().search(query)
    
    def homepage_feed(self):
        """
        Optimized query for homepage feed with all necessary relations
        and counts preloaded.
        """
        from django.db.models import Prefetch
        from django.contrib.auth.models import User
        
        # Get active comments with their authors (avoid circular import)
        from django.apps import apps
        Comment = apps.get_model('posts', 'Comment')
        
        active_comments = Comment.objects.filter(active=True).select_related(
            'author', 'author__profile'
        )
        
        return self.filter(status="published").select_related(
            'author', 'author__profile'
        ).prefetch_related(
            Prefetch('comments', queryset=active_comments),
            'tags',
            'likes',
            'favorites'
        ).annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            favorites_count=Count('favorites', distinct=True)
        ).order_by('-is_sticky', '-created_at')
    
    def user_feed(self, user):
        """
        Optimized query for user feed based on followed authors.
        """
        if not user.is_authenticated:
            return self.homepage_feed()
            
        # Get authors followed by the user
        followed_authors = user.profile.follows.values_list('user', flat=True)
        
        return self.filter(status="published").select_related(
            'author', 'author__profile'
        ).prefetch_related(
            'comments__author__profile',
            'tags',
            'likes',
            'favorites'
        ).annotate(
            likes_count=Count('likes', distinct=True),
            comments_count=Count('comments', distinct=True),
            favorites_count=Count('favorites', distinct=True)
        ).filter(
            author__in=followed_authors
        ).order_by('-created_at')
    
    def with_related_posts(self, limit=3):
        """
        Include related posts based on tags.
        """
        from django.db.models import Count, Case, When, Value, IntegerField
        
        def get_related_posts(post):
            # Get posts with the same tags, excluding the current post
            post_tags = post.tags.values_list('id', flat=True)
            
            if not post_tags:
                return self.none()
                
            return self.filter(status="published").exclude(id=post.id).filter(
                tags__id__in=post_tags
            ).annotate(
                same_tags=Count('tags', filter=Q(tags__id__in=post_tags))
            ).order_by('-same_tags', '-created_at')[:limit]
        
        return get_related_posts
    
    def with_comments_paginated(self, post_id, page=1, per_page=10):
        """
        Get a post with paginated comments.
        """
        from django.core.paginator import Paginator
        
        post = self.select_related('author', 'author__profile').get(id=post_id)
        
        # Get active comments with their authors (avoid circular import)
        from django.apps import apps
        Comment = apps.get_model('posts', 'Comment')
        
        comments = Comment.objects.filter(
            post=post, active=True
        ).select_related(
            'author', 'author__profile'
        ).prefetch_related(
            'likes'
        ).order_by('-created_at')
        
        # Paginate comments
        paginator = Paginator(comments, per_page)
        comments_page = paginator.get_page(page)
        
        return post, comments_page


class CommentManager(models.Manager):
    """
    Manager optimizado para el modelo Comment con métodos que utilizan
    select_related para evitar problemas N+1.
    """
    
    def get_queryset(self):
        """Return custom QuerySet."""
        return CommentQuerySet(self.model, using=self._db)
    
    def active(self):
        """Retorna solo comentarios activos."""
        return self.get_queryset().active()
    
    def with_author(self):
        """Incluye el autor en una sola consulta."""
        return self.get_queryset().with_author()
    
    def with_post_info(self):
        """Include post information with comments."""
        return self.get_queryset().with_post_info()
    
    def with_likes(self):
        """Añade conteo de likes como anotación."""
        return self.get_queryset().with_likes()
    
    def for_post(self, post):
        """Retorna comentarios para un post específico con sus autores."""
        return self.get_queryset().active().with_author().filter(post=post).order_by('-created_at')
    
    def recent_with_context(self, limit=20):
        """Get recent comments with full context."""
        return self.get_queryset().active().with_post_info().prefetch_related(
            'likes'
        ).order_by('-created_at')[:limit]
    
    def by_user_with_context(self, user):
        """Get comments by a specific user with full context."""
        return self.get_queryset().active().with_post_info().filter(
            author=user
        ).prefetch_related(
            'likes'
        ).order_by('-created_at')
    
    def most_liked(self, limit=10):
        """Get most liked comments."""
        return self.get_queryset().active().with_post_info().with_likes().order_by(
            '-likes_count', '-created_at'
        )[:limit]
    
    def with_user_like_status(self, user):
        """
        Annotate comments with whether the current user has liked them.
        """
        from django.db.models import Exists, OuterRef
        
        if not user.is_authenticated:
            return self.get_queryset()
            
        return self.get_queryset().annotate(
            liked_by_user=Exists(
                self.model.likes.through.objects.filter(
                    user_id=user.id,
                    comment_id=OuterRef('pk')
                )
            )
        )