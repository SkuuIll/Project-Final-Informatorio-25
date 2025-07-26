from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django import forms
from django.utils.html import format_html
from django.core.files.storage import default_storage
import logging
from .models import Post, Comment, AIModel
from .forms import AiPostGeneratorForm
from .widgets import ImageSelectorWidget
from .utils import safe_get_image_url, validate_image_file, log_file_error
from .admin_extensions import ImageGalleryAdminMixin, add_image_gallery_to_admin
# El import de ai_generator_optimized se hace dinámicamente en la vista

logger = logging.getLogger(__name__)

class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    actions = ['activate_model']

    def activate_model(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Solo puedes activar un modelo a la vez.", level=messages.ERROR)
            return
        model = queryset.first()
        model.is_active = True
        model.save()
        self.message_user(request, f"El modelo {model.name} ha sido activado.", level=messages.SUCCESS)

    activate_model.short_description = "Activar modelo seleccionado"

admin.site.register(AIModel, AIModelAdmin)

class FlexibleImageField(forms.CharField):
    """Campo personalizado que acepta tanto archivos como strings (paths de imágenes)."""
    
    def __init__(self, *args, **kwargs):
        kwargs['required'] = False
        super().__init__(*args, **kwargs)
        self.widget = ImageSelectorWidget()
    
    def to_python(self, value):
        """Convertir el valor a un formato que Django pueda manejar."""
        if not value:
            return None
        
        # Si es un string (imagen seleccionada), retornarlo tal como está
        if isinstance(value, str):
            return value
            
        # Si es un archivo subido, procesarlo normalmente
        return value

class PostAdminForm(forms.ModelForm):
    """Formulario personalizado para el admin de Post."""
    
    # Reemplazar el campo header_image con nuestro campo personalizado
    header_image = FlexibleImageField(label="Imagen de cabecera")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = Post
        fields = '__all__'
    
    def is_multipart(self):
        """Asegurar que el formulario use enctype multipart/form-data"""
        return True
    
    def clean_header_image(self):
        """Validar y procesar el campo header_image."""
        header_image = self.cleaned_data.get('header_image')
        
        # Si es un string (imagen seleccionada), validar que existe
        if isinstance(header_image, str) and header_image:
            from django.core.files.storage import default_storage
            if default_storage.exists(header_image):
                return header_image
            else:
                raise forms.ValidationError(f"La imagen seleccionada no existe: {header_image}")
        
        # Si es un archivo subido o None, procesarlo normalmente
        return header_image

@admin.register(Post)
class PostAdmin(ImageGalleryAdminMixin, admin.ModelAdmin):
    """Configuración del panel de administración para los Posts."""
    form = PostAdminForm
    list_display = ("title", "author", "status", "created_at", "views", "is_sticky", "safe_header_image_display", "get_image_gallery_link")
    list_filter = ("status", "created_at", "author", "is_sticky")
    search_fields = ("title", "content")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    change_list_template = "admin/posts/post/change_list.html"
    
    def save_model(self, request, obj, form, change):
        """Sobrescribir save_model para manejar la selección de imágenes."""
        # Verificar si se seleccionó una imagen existente
        header_image_data = form.cleaned_data.get('header_image')
        
        # Si es un string (imagen seleccionada), asignarlo directamente
        if isinstance(header_image_data, str) and header_image_data:
            obj.header_image = header_image_data
        
        # Guardar el objeto
        super().save_model(request, obj, form, change)
    
    def safe_header_image_display(self, obj):
        """
        Safely display header image thumbnail in admin list view.
        
        Args:
            obj (Post): Post instance
            
        Returns:
            str: HTML for image display with proper error handling
        """
        try:
            # Check if post has header_image field
            if not hasattr(obj, 'header_image'):
                return format_html('<span style="color: #6c757d;">No disponible</span>')
            
            header_image = obj.header_image
            
            # Handle None or empty values
            if not header_image:
                return format_html('<span style="color: #6c757d;">Sin imagen</span>')
            
            # Check if it's a string (file path) or file field
            if isinstance(header_image, str):
                if not header_image.strip():
                    return format_html('<span style="color: #6c757d;">Sin imagen</span>')
                
                # Validate file exists
                validation = validate_image_file(header_image)
                if validation['valid']:
                    try:
                        image_url = default_storage.url(header_image)
                        return format_html(
                            '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" title="{}" />',
                            image_url,
                            header_image
                        )
                    except Exception as e:
                        log_file_error("admin list display URL generation", header_image, e, 'warning')
                        return format_html('<span style="color: #dc3545;" title="{}">URL inválida</span>', str(e))
                else:
                    return format_html(
                        '<span style="color: #dc3545;" title="{}">Archivo no encontrado</span>',
                        validation['message']
                    )
            
            # Handle file field objects
            elif hasattr(header_image, 'name'):
                if not header_image.name:
                    return format_html('<span style="color: #6c757d;">Sin imagen</span>')
                
                # Use safe utility function
                image_url = safe_get_image_url(header_image)
                if image_url:
                    return format_html(
                        '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" title="{}" />',
                        image_url,
                        header_image.name
                    )
                else:
                    # File field exists but URL cannot be generated
                    validation = validate_image_file(header_image.name)
                    if not validation['valid']:
                        return format_html(
                            '<span style="color: #dc3545;" title="{}">Imagen inválida</span>',
                            validation['message']
                        )
                    else:
                        return format_html('<span style="color: #ffc107;">Error de acceso</span>')
            
            # Unknown type
            else:
                logger.warning(f"Unknown header_image type for post {obj.id}: {type(header_image)}")
                return format_html('<span style="color: #dc3545;">Tipo desconocido</span>')
                
        except Exception as e:
            log_file_error(f"admin list display for post {obj.id}", getattr(obj, 'header_image', None), e, 'error')
            return format_html('<span style="color: #dc3545;" title="{}">Error</span>', str(e))
    
    safe_header_image_display.short_description = "Imagen"
    safe_header_image_display.admin_order_field = "header_image"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "generate-ai/",
                self.admin_site.admin_view(self.generate_ai_post_view),
                name="post_generate_ai",
            ),
        ]
        return custom_urls + urls

    def generate_ai_post_view(self, request):
        if request.method == "POST":
            form = AiPostGeneratorForm(request.POST)
            if form.is_valid():
                url = form.cleaned_data['url']
                rewrite_prompt = form.cleaned_data['rewrite_prompt']
                extract_images = form.cleaned_data.get('extract_images', True)
                max_images = min(form.cleaned_data.get('max_images', 3), 3)  # Máximo 3 para evitar timeouts

                try:
                    # Usar generador original con configuración optimizada
                    from .ai_generator import generate_complete_post
                    
                    result = generate_complete_post(
                        url=url, 
                        rewrite_prompt=rewrite_prompt, 
                        extract_images=extract_images, 
                        max_images=max_images,
                        generate_cover=False  # Desactivar para evitar timeouts
                    )
                    
                    if not result.get('success'):
                        error_msg = result.get('error', 'Error desconocido')
                        logger.error(f"Error generando post en admin: {error_msg}")
                        self.message_user(request, f"No se pudo generar el post: {error_msg}", level=messages.ERROR)
                        return redirect(".")

                    title = result.get('title', 'Título no generado')
                    content = result.get('content', '')
                    tags = result.get('tags', [])
                    reading_time = result.get('reading_time', 5)

                    post = Post.objects.create(
                        author=request.user,
                        title=title,
                        content=content,
                        status='draft',
                        reading_time=reading_time
                    )
                    
                    if tags:
                        post.tags.add(*tags)

                    logger.info(f"Post generado exitosamente en admin: {post.id} por {request.user.username}")
                    self.message_user(request, "Post generado con éxito como borrador. Ya puedes editarlo.", level=messages.SUCCESS)
                    return redirect("admin:posts_post_change", post.id)

                except TimeoutError:
                    error_msg = "La generación del post excedió el tiempo límite. Intenta con contenido más corto o sin imágenes."
                    logger.error(f"Timeout en generación de post admin: {request.user.username}")
                    self.message_user(request, error_msg, level=messages.ERROR)
                    return redirect(".")
                except Exception as e:
                    logger.error(f"Error inesperado en generación admin: {e}", exc_info=True)
                    self.message_user(request, f"Ocurrió un error inesperado: {str(e)}", level=messages.ERROR)
                    return redirect(".")
        else:
            form = AiPostGeneratorForm()

        context = dict(
           self.admin_site.each_context(request),
           form=form,
           title="Generar Post con IA (Optimizado)",
        )
        return render(request, "admin/posts/post/ai_generator.html", context)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para los Comentarios."""
    list_display = ("author", "post", "created_at", "active")
    list_filter = ("active", "created_at")
    search_fields = ("author__username", "body")
    actions = ["approve_comments"]

    def approve_comments(self, request, queryset):
        queryset.update(active=True)

    approve_comments.short_description = "Aprobar comentarios seleccionados"

# Inicializar extensiones del admin
add_image_gallery_to_admin()