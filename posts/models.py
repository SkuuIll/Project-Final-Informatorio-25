from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from taggit.managers import TaggableManager
import re
from django.utils.html import strip_tags
from .managers import PostManager, CommentManager, AIModelManager


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