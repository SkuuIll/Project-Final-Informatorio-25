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


# ============================================================================
# MANAGERS PARA SISTEMA DE TAGS INTELIGENTE
# ============================================================================

class TagMetadataQuerySet(models.QuerySet):
    """
    Custom QuerySet for TagMetadata model.
    """
    
    def approved(self):
        """Retorna solo tags aprobados."""
        return self.filter(is_approved=True)
    
    def trending(self):
        """Retorna solo tags en tendencia."""
        return self.filter(is_trending=True)
    
    def popular(self, limit=20):
        """Retorna tags más populares."""
        return self.approved().order_by('-usage_count')[:limit]
    
    def by_category(self, category):
        """Filtra por categoría."""
        return self.approved().filter(category=category)
    
    def with_tag_info(self):
        """Incluye información del tag relacionado."""
        return self.select_related('tag', 'created_by')
    
    def recent_activity(self, days=7):
        """Tags con actividad reciente."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(last_used__gte=cutoff_date)
    
    def calculate_trending(self, days=7):
        """Calcula trending score basado en uso reciente."""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count, F, Case, When, Value
        
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return self.annotate(
            recent_usage=Count(
                'tag__usage_history',
                filter=Q(tag__usage_history__used_at__gte=cutoff_date)
            )
        ).annotate(
            calculated_trending_score=Case(
                When(usage_count=0, then=Value(0.0)),
                default=F('recent_usage') * 1.0 / F('usage_count'),
                output_field=models.FloatField()
            )
        )


class TagMetadataManager(models.Manager):
    """
    Manager optimizado para TagMetadata.
    """
    
    def get_queryset(self):
        return TagMetadataQuerySet(self.model, using=self._db)
    
    def approved(self):
        return self.get_queryset().approved()
    
    def trending(self):
        return self.get_queryset().trending()
    
    def popular(self, limit=20):
        return self.get_queryset().popular(limit)
    
    def by_category(self, category):
        return self.get_queryset().by_category(category)
    
    def with_tag_info(self):
        return self.get_queryset().with_tag_info()
    
    def recent_activity(self, days=7):
        return self.get_queryset().recent_activity(days)
    
    def get_or_create_for_tag(self, tag, user=None):
        """Obtiene o crea metadata para un tag."""
        metadata, created = self.get_or_create(
            tag=tag,
            defaults={
                'created_by': user,
                'usage_count': 0,
                'trending_score': 0.0,
            }
        )
        return metadata, created
    
    def update_usage_count(self, tag):
        """Actualiza el contador de uso de un tag."""
        metadata, created = self.get_or_create_for_tag(tag)
        metadata.usage_count = F('usage_count') + 1
        metadata.save(update_fields=['usage_count'])
        return metadata
    
    def calculate_trending_scores(self, days=7):
        """Calcula y actualiza trending scores para todos los tags."""
        trending_data = self.get_queryset().calculate_trending(days)
        
        for metadata in trending_data:
            if hasattr(metadata, 'calculated_trending_score'):
                metadata.trending_score = metadata.calculated_trending_score
                metadata.is_trending = metadata.calculated_trending_score > 0.1  # Threshold
                metadata.save(update_fields=['trending_score', 'is_trending'])


class TagSynonymQuerySet(models.QuerySet):
    """
    Custom QuerySet for TagSynonym model.
    """
    
    def active(self):
        """Retorna solo sinónimos activos."""
        return self.filter(is_active=True)
    
    def for_tag(self, tag):
        """Retorna sinónimos para un tag específico."""
        return self.active().filter(main_tag=tag)
    
    def with_main_tag(self):
        """Incluye información del tag principal."""
        return self.select_related('main_tag', 'created_by')


class TagSynonymManager(models.Manager):
    """
    Manager para TagSynonym.
    """
    
    def get_queryset(self):
        return TagSynonymQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def for_tag(self, tag):
        return self.get_queryset().for_tag(tag)
    
    def with_main_tag(self):
        return self.get_queryset().with_main_tag()
    
    def find_main_tag(self, synonym_text):
        """Encuentra el tag principal para un sinónimo."""
        try:
            synonym = self.active().get(synonym_text__iexact=synonym_text)
            return synonym.main_tag
        except self.model.DoesNotExist:
            return None
    
    def create_synonym(self, main_tag, synonym_text, user):
        """Crea un nuevo sinónimo con validación."""
        from django.core.exceptions import ValidationError
        
        # Normalizar texto
        synonym_text = synonym_text.lower().strip()
        
        # Verificar que no exista ya
        if self.filter(synonym_text__iexact=synonym_text).exists():
            raise ValidationError(f"El sinónimo '{synonym_text}' ya existe")
        
        # Verificar que no sea igual al tag principal
        if synonym_text == main_tag.name.lower():
            raise ValidationError("El sinónimo no puede ser igual al tag principal")
        
        return self.create(
            main_tag=main_tag,
            synonym_text=synonym_text,
            created_by=user
        )


class TagCooccurrenceQuerySet(models.QuerySet):
    """
    Custom QuerySet for TagCooccurrence model.
    """
    
    def for_tag(self, tag):
        """Retorna coocurrencias para un tag específico."""
        return self.filter(Q(tag1=tag) | Q(tag2=tag))
    
    def strong_relations(self, threshold=0.1):
        """Retorna solo relaciones fuertes."""
        return self.filter(strength__gte=threshold)
    
    def ordered_by_strength(self):
        """Ordena por fuerza de relación."""
        return self.order_by('-strength', '-count')
    
    def with_tags(self):
        """Incluye información de ambos tags."""
        return self.select_related('tag1', 'tag2')


class TagCooccurrenceManager(models.Manager):
    """
    Manager para TagCooccurrence.
    """
    
    def get_queryset(self):
        return TagCooccurrenceQuerySet(self.model, using=self._db)
    
    def for_tag(self, tag):
        return self.get_queryset().for_tag(tag)
    
    def strong_relations(self, threshold=0.1):
        return self.get_queryset().strong_relations(threshold)
    
    def ordered_by_strength(self):
        return self.get_queryset().ordered_by_strength()
    
    def with_tags(self):
        return self.get_queryset().with_tags()
    
    def get_related_tags(self, tag, limit=10):
        """Obtiene tags relacionados para un tag específico."""
        cooccurrences = self.for_tag(tag).strong_relations().ordered_by_strength().with_tags()[:limit]
        
        related_tags = []
        for cooccurrence in cooccurrences:
            # Determinar cuál es el tag relacionado
            related_tag = cooccurrence.tag2 if cooccurrence.tag1 == tag else cooccurrence.tag1
            related_tags.append({
                'tag': related_tag,
                'strength': cooccurrence.strength,
                'count': cooccurrence.count
            })
        
        return related_tags
    
    def update_cooccurrence(self, tag1, tag2):
        """Actualiza o crea una coocurrencia entre dos tags."""
        # Asegurar orden consistente (tag1.id < tag2.id)
        if tag1.id > tag2.id:
            tag1, tag2 = tag2, tag1
        
        cooccurrence, created = self.get_or_create(
            tag1=tag1,
            tag2=tag2,
            defaults={'count': 1}
        )
        
        if not created:
            cooccurrence.count = F('count') + 1
            cooccurrence.save(update_fields=['count'])
        
        return cooccurrence
    
    def update_from_post_tags(self, tags):
        """Actualiza coocurrencias basado en tags de un post."""
        tag_list = list(tags)
        
        # Crear coocurrencias para cada par de tags
        for i, tag1 in enumerate(tag_list):
            for tag2 in tag_list[i+1:]:
                self.update_cooccurrence(tag1, tag2)


class TagUsageHistoryQuerySet(models.QuerySet):
    """
    Custom QuerySet for TagUsageHistory model.
    """
    
    def for_tag(self, tag):
        """Retorna historial para un tag específico."""
        return self.filter(tag=tag)
    
    def for_user(self, user):
        """Retorna historial para un usuario específico."""
        return self.filter(user=user)
    
    def recent(self, days=30):
        """Retorna uso reciente."""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(used_at__gte=cutoff_date)
    
    def with_relations(self):
        """Incluye relaciones con tag, post y usuario."""
        return self.select_related('tag', 'post', 'user')


class TagUsageHistoryManager(models.Manager):
    """
    Manager para TagUsageHistory.
    """
    
    def get_queryset(self):
        return TagUsageHistoryQuerySet(self.model, using=self._db)
    
    def for_tag(self, tag):
        return self.get_queryset().for_tag(tag)
    
    def for_user(self, user):
        return self.get_queryset().for_user(user)
    
    def recent(self, days=30):
        return self.get_queryset().recent(days)
    
    def with_relations(self):
        return self.get_queryset().with_relations()
    
    def record_usage(self, tag, post, user):
        """Registra el uso de un tag."""
        return self.create(
            tag=tag,
            post=post,
            user=user
        )
    
    def get_user_tag_history(self, user, limit=50):
        """Obtiene historial de tags de un usuario."""
        return self.for_user(user).with_relations().order_by('-used_at')[:limit]
    
    def get_trending_tags(self, days=7, limit=20):
        """Obtiene tags trending basado en uso reciente."""
        from django.db.models import Count
        
        return self.recent(days).values('tag').annotate(
            usage_count=Count('tag')
        ).order_by('-usage_count')[:limit]