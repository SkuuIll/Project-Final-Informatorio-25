from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from ckeditor.fields import RichTextField 

class Post(models.Model):
    title = models.CharField(max_length=200, verbose_name="Título")
    
    header_image = models.ImageField(
        upload_to='post_images/', 
        null=True, 
        blank=True, 
        verbose_name="Imagen de cabecera"
    )

    content = RichTextField(blank=True, null=True, verbose_name="Contenido")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.id)])

    class Meta:
        ordering = ['-created_at']
