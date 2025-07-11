from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.text import slugify 
from django_ckeditor_5.fields import CKEditor5Field
from taggit.managers import TaggableManager

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Borrador'),
        ('published', 'Publicado'),
    )
    title = models.CharField(max_length=200, verbose_name="Título")
    
    header_image = models.ImageField(
        upload_to='post_images/', 
        null=True, 
        blank=True, 
        verbose_name="Imagen de cabecera"
    )

    content = CKEditor5Field(blank=True, null=True, verbose_name="Contenido")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    
    slug = models.SlugField(unique=True, max_length=200, editable=False)
    views = models.PositiveIntegerField(default=0, verbose_name="Vistas")
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    favorites = models.ManyToManyField(User, related_name='favorite_posts', blank=True)
    tags = TaggableManager(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Estado")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('posts:post_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="Post")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")
    content = models.TextField(verbose_name="Contenido")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    active = models.BooleanField(default=True, verbose_name="Activo")

    def __str__(self):
        return f'Comentario de {self.author.username} en {self.post.title}'
