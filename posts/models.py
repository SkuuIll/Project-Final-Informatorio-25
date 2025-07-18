from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from taggit.managers import TaggableManager
import re
from django.utils.html import strip_tags
from django.utils import timezone


class Post(models.Model):
    STATUS_CHOICES = (
        ("draft", "Borrador"),
        ("published", "Publicado"),
    )
    title = models.CharField(max_length=200, verbose_name="Título")

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

    @property
    def is_new(self):
        return (timezone.now() - self.created_at).days < 7

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


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Post"
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Autor", related_name="comments_by_author"
    )
    content = models.TextField(verbose_name="Contenido")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de creación"
    )
    active = models.BooleanField(default=True, verbose_name="Activo")
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)

    def __str__(self):
        return f"Comentario de {self.author.username} en {self.post.title}"