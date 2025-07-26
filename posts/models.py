from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from taggit.managers import TaggableManager
from taggit.models import Tag
import re
from django.utils.html import strip_tags
from .managers import (
    PostManager, CommentManager, AIModelManager,
    TagMetadataManager, TagSynonymManager, TagCooccurrenceManager, TagUsageHistoryManager
)


class Post(models.Model):
    STATUS_CHOICES = (
        ("draft", "Borrador"),
        ("published", "Publicado"),
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    
    # Managers
    objects = models.Manager()  # Default manager
    optimized = PostManager()  # Optimized manager

    header_image = models.ImageField(
        upload_to="post_images/",
        null=True,
        blank=True,
        verbose_name="Imagen de cabecera",
    )

    content = CKEditor5Field(blank=True, null=True, verbose_name="Contenido")

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Autor", related_name="posts"
    )

    slug = models.SlugField(unique=True, max_length=200, editable=False)
    views = models.PositiveIntegerField(default=0, verbose_name="Vistas")
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    favorites = models.ManyToManyField(User, related_name="favorite_posts", blank=True)
    tags = TaggableManager(blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="draft", verbose_name="Estado"
    )
    reading_time = models.PositiveIntegerField(default=0, verbose_name="Tiempo de lectura")
    is_sticky = models.BooleanField(default=False, verbose_name="Destacado")
    
    # Campos para optimización de rendimiento
    cached_likes_count = models.PositiveIntegerField(default=0, verbose_name="Contador de likes en caché")
    cached_comments_count = models.PositiveIntegerField(default=0, verbose_name="Contador de comentarios en caché")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Última actividad")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("posts:post_detail", kwargs={"username": self.author.username, "slug": self.slug})

    def calculate_reading_time(self):
        if self.content:
            text = strip_tags(self.content)
            word_count = len(re.findall(r'\w+', text))
            reading_speed = 200  # Palabras por minuto
            return max(1, round(word_count / reading_speed))
        return 0

    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            original_slug = self.slug
            queryset = Post.objects.all().exclude(pk=self.pk)
            counter = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        
        self.reading_time = self.calculate_reading_time()
        
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Core query patterns
            models.Index(fields=['status', '-created_at'], name='post_status_created'),
            models.Index(fields=['author', 'status'], name='post_author_status'),
            models.Index(fields=['slug'], name='post_slug_unique'),
            
            # Popular content queries
            models.Index(fields=['-views'], name='post_views_desc'),
            models.Index(fields=['-views', 'status'], name='post_popular_published'),
            
            # Sticky posts
            models.Index(fields=['is_sticky', '-created_at'], name='post_sticky_recent'),
            models.Index(fields=['is_sticky', 'status', '-created_at'], name='post_sticky_published'),
            
            # Search and filtering
            models.Index(fields=['status', 'author', '-created_at'], name='post_author_published'),
            models.Index(fields=['created_at'], name='post_created_at'),
            
            # Reading time and engagement
            models.Index(fields=['reading_time'], name='post_reading_time'),
            models.Index(fields=['status', '-reading_time'], name='post_by_reading_time'),
        ]


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Post"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Autor", related_name="comments_by_author"
    )
    
    # Managers
    objects = models.Manager()  # Default manager
    optimized = CommentManager()  # Optimized manager
    content = models.TextField(verbose_name="Contenido")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    active = models.BooleanField(default=True, verbose_name="Activo")
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)

    def __str__(self):
        return f"Comentario de {self.author.username} en {self.post.title}"
        
    class Meta:
        indexes = [
            # Core comment queries
            models.Index(fields=['post', '-created_at'], name='comment_post_recent'),
            models.Index(fields=['author', '-created_at'], name='comment_author_recent'),
            models.Index(fields=['active'], name='comment_active'),
            
            # Moderation and filtering
            models.Index(fields=['active', 'post'], name='comment_active_post'),
            models.Index(fields=['active', '-created_at'], name='comment_active_recent'),
            models.Index(fields=['post', 'active', '-created_at'], name='comment_post_active_recent'),
            
            # Author activity
            models.Index(fields=['author', 'active'], name='comment_author_active'),
        ]

class AIModel(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Modelo")
    is_active = models.BooleanField(default=False, verbose_name="Activo")
    
    # Managers
    objects = models.Manager()  # Default manager
    optimized = AIModelManager()  # Optimized manager

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_active:
            AIModel.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Modelo de IA"
        verbose_name_plural = "Modelos de IA"


class AIPromptTemplate(models.Model):
    PROMPT_TYPES = [
        ('content', 'Generación de Contenido'),
        ('tags', 'Generación de Tags'),
        ('image', 'Generación de Imagen'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Nombre del Template")
    prompt_type = models.CharField(max_length=20, choices=PROMPT_TYPES, verbose_name="Tipo de Prompt")
    template = models.TextField(verbose_name="Template del Prompt")
    description = models.TextField(blank=True, verbose_name="Descripción")
    is_default = models.BooleanField(default=False, verbose_name="Por Defecto")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Creado por")

    def __str__(self):
        return f"{self.name} ({self.get_prompt_type_display()})"

    def save(self, *args, **kwargs):
        # Solo puede haber un template por defecto por tipo
        if self.is_default:
            AIPromptTemplate.objects.filter(
                prompt_type=self.prompt_type, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Template de Prompt de IA"
        verbose_name_plural = "Templates de Prompts de IA"
        unique_together = ['name', 'prompt_type']
        indexes = [
            models.Index(fields=['prompt_type', 'is_default'], name='prompt_type_default'),
            models.Index(fields=['is_active'], name='prompt_active'),
        ]


# ============================================================================
# SISTEMA DE TAGS INTELIGENTE - MODELOS EXTENDIDOS
# ============================================================================

class TagMetadata(models.Model):
    """
    Metadatos extendidos para tags del sistema inteligente.
    Almacena estadísticas de uso, trending y información adicional.
    """
    tag = models.OneToOneField(
        Tag, 
        on_delete=models.CASCADE, 
        related_name='metadata',
        verbose_name="Tag"
    )
    usage_count = models.PositiveIntegerField(
        default=0, 
        verbose_name="Contador de uso",
        help_text="Número total de veces que se ha usado este tag"
    )
    trending_score = models.FloatField(
        default=0.0, 
        verbose_name="Puntuación trending",
        help_text="Score calculado para determinar si el tag está en tendencia"
    )
    last_used = models.DateTimeField(
        auto_now=True, 
        verbose_name="Último uso",
        help_text="Fecha y hora del último uso del tag"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Creado por",
        help_text="Usuario que creó este tag"
    )
    is_approved = models.BooleanField(
        default=True, 
        verbose_name="Aprobado",
        help_text="Indica si el tag ha sido aprobado por moderadores"
    )
    is_trending = models.BooleanField(
        default=False, 
        verbose_name="En tendencia",
        help_text="Indica si el tag está actualmente en tendencia"
    )
    category = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Categoría",
        help_text="Categoría temática del tag (ej: tecnología, programación)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    # Managers
    objects = models.Manager()  # Default manager
    optimized = TagMetadataManager()  # Optimized manager

    def __str__(self):
        return f"Metadata: {self.tag.name} (uso: {self.usage_count})"

    class Meta:
        verbose_name = "Metadatos de Tag"
        verbose_name_plural = "Metadatos de Tags"
        indexes = [
            # Consultas por popularidad
            models.Index(fields=['-usage_count'], name='tagmeta_usage_desc'),
            models.Index(fields=['-trending_score'], name='tagmeta_trending_desc'),
            
            # Consultas por estado
            models.Index(fields=['is_trending'], name='tagmeta_trending'),
            models.Index(fields=['is_approved'], name='tagmeta_approved'),
            
            # Consultas temporales
            models.Index(fields=['-last_used'], name='tagmeta_last_used'),
            models.Index(fields=['-created_at'], name='tagmeta_created'),
            
            # Consultas combinadas
            models.Index(fields=['is_approved', '-usage_count'], name='tagmeta_approved_popular'),
            models.Index(fields=['is_trending', '-trending_score'], name='tagmeta_trending_score'),
            models.Index(fields=['category', '-usage_count'], name='tagmeta_category_popular'),
        ]


class TagSynonym(models.Model):
    """
    Gestión de sinónimos de tags para evitar duplicación.
    Permite definir relaciones de sinonimia entre términos.
    """
    main_tag = models.ForeignKey(
        Tag, 
        on_delete=models.CASCADE, 
        related_name='synonyms',
        verbose_name="Tag principal",
        help_text="Tag principal al que se redirigirán los sinónimos"
    )
    synonym_text = models.CharField(
        max_length=100, 
        unique=True,
        verbose_name="Texto del sinónimo",
        help_text="Texto alternativo que será redirigido al tag principal"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Creado por",
        help_text="Usuario que definió este sinónimo"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el sinónimo está activo"
    )

    # Managers
    objects = models.Manager()  # Default manager
    optimized = TagSynonymManager()  # Optimized manager

    def __str__(self):
        return f"'{self.synonym_text}' → '{self.main_tag.name}'"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validar que el sinónimo no sea igual al tag principal
        if self.synonym_text.lower() == self.main_tag.name.lower():
            raise ValidationError("El sinónimo no puede ser igual al tag principal")
        
        # Validar que no exista ya un tag con ese nombre
        if Tag.objects.filter(name__iexact=self.synonym_text).exists():
            raise ValidationError("Ya existe un tag con ese nombre")

    class Meta:
        verbose_name = "Sinónimo de Tag"
        verbose_name_plural = "Sinónimos de Tags"
        indexes = [
            models.Index(fields=['synonym_text'], name='tagsynonym_text'),
            models.Index(fields=['main_tag', 'is_active'], name='tagsynonym_main_active'),
            models.Index(fields=['-created_at'], name='tagsynonym_created'),
        ]


class TagCooccurrence(models.Model):
    """
    Matriz de coocurrencia de tags para recomendaciones.
    Almacena qué tags aparecen frecuentemente juntos.
    """
    tag1 = models.ForeignKey(
        Tag, 
        on_delete=models.CASCADE, 
        related_name='cooccurrences_as_tag1',
        verbose_name="Tag 1"
    )
    tag2 = models.ForeignKey(
        Tag, 
        on_delete=models.CASCADE, 
        related_name='cooccurrences_as_tag2',
        verbose_name="Tag 2"
    )
    count = models.PositiveIntegerField(
        default=1,
        verbose_name="Contador",
        help_text="Número de veces que estos tags han aparecido juntos"
    )
    strength = models.FloatField(
        default=0.0,
        verbose_name="Fuerza de relación",
        help_text="Fuerza de la relación entre los tags (0-1)"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    # Managers
    objects = models.Manager()  # Default manager
    optimized = TagCooccurrenceManager()  # Optimized manager

    def __str__(self):
        return f"{self.tag1.name} + {self.tag2.name} (count: {self.count}, strength: {self.strength:.2f})"

    def calculate_strength(self):
        """
        Calcula la fuerza de la relación basada en:
        - Frecuencia de coocurrencia
        - Popularidad individual de cada tag
        """
        try:
            tag1_usage = self.tag1.metadata.usage_count if hasattr(self.tag1, 'metadata') else 1
            tag2_usage = self.tag2.metadata.usage_count if hasattr(self.tag2, 'metadata') else 1
            
            # Fórmula: count / sqrt(usage_tag1 * usage_tag2)
            # Normaliza por la popularidad individual de cada tag
            import math
            self.strength = self.count / math.sqrt(tag1_usage * tag2_usage)
            self.strength = min(self.strength, 1.0)  # Limitar a máximo 1.0
        except (AttributeError, ZeroDivisionError):
            self.strength = 0.0

    def save(self, *args, **kwargs):
        # Asegurar que tag1 siempre tenga ID menor que tag2 para evitar duplicados
        if self.tag1.id > self.tag2.id:
            self.tag1, self.tag2 = self.tag2, self.tag1
        
        self.calculate_strength()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Coocurrencia de Tags"
        verbose_name_plural = "Coocurrencias de Tags"
        unique_together = ['tag1', 'tag2']
        indexes = [
            # Consultas por tag específico
            models.Index(fields=['tag1', '-strength'], name='tagcooccur_tag1_strength'),
            models.Index(fields=['tag2', '-strength'], name='tagcooccur_tag2_strength'),
            
            # Consultas por fuerza de relación
            models.Index(fields=['-strength'], name='tagcooccur_strength_desc'),
            models.Index(fields=['-count'], name='tagcooccur_count_desc'),
            
            # Consultas temporales
            models.Index(fields=['-last_updated'], name='tagcooccur_updated'),
        ]


class TagUsageHistory(models.Model):
    """
    Historial de uso de tags para análisis temporal y trending.
    Permite calcular tendencias basadas en uso reciente.
    """
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name='usage_history',
        verbose_name="Tag"
    )
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='tag_usage_history',
        verbose_name="Post"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    used_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de uso"
    )
    
    # Managers
    objects = models.Manager()  # Default manager
    optimized = TagUsageHistoryManager()  # Optimized manager
    
    def __str__(self):
        return f"{self.tag.name} usado en '{self.post.title}' por {self.user.username}"

    class Meta:
        verbose_name = "Historial de Uso de Tag"
        verbose_name_plural = "Historiales de Uso de Tags"
        indexes = [
            # Consultas por tag y tiempo
            models.Index(fields=['tag', '-used_at'], name='taghistory_tag_time'),
            
            # Consultas temporales para trending
            models.Index(fields=['-used_at'], name='taghistory_time_desc'),
            models.Index(fields=['used_at'], name='taghistory_time_asc'),
            
            # Consultas por usuario
            models.Index(fields=['user', '-used_at'], name='taghistory_user_time'),
            
            # Consultas por post
            models.Index(fields=['post'], name='taghistory_post'),
        ]