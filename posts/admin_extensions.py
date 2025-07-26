"""
Extensiones para el admin de Django.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

class ImageGalleryAdminMixin:
    """
    Mixin para agregar enlaces a la galería de imágenes en el admin.
    """
    
    def get_image_gallery_link(self, obj=None):
        """
        Genera un enlace a la galería de imágenes.
        """
        url = reverse('posts:image_gallery')
        return format_html(
            '<a href="{}" class="button" target="_blank" style="margin-left: 10px;">'
            '<i class="fas fa-images"></i> Galería de Imágenes</a>',
            url
        )
    
    get_image_gallery_link.short_description = "Galería"
    get_image_gallery_link.allow_tags = True

def add_image_gallery_to_admin():
    """
    Agrega enlaces a la galería de imágenes en el admin.
    """
    # Agregar CSS y JS personalizados
    admin.site.index_template = 'admin/custom_index.html'
    
    # Agregar enlace en el header del admin
    original_each_context = admin.site.each_context
    
    def custom_each_context(request):
        context = original_each_context(request)
        context['image_gallery_url'] = reverse('posts:image_gallery')
        return context
    
    admin.site.each_context = custom_each_context