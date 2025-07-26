"""
Widgets personalizados para el admin de Django.
"""
import os
import logging
from django import forms
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils.safestring import mark_safe
from django.urls import reverse
import json
from .utils import safe_get_image_url, validate_image_file, log_file_error

logger = logging.getLogger(__name__)

class ImageSelectorWidget(forms.ClearableFileInput):
    """
    Widget personalizado que permite seleccionar una imagen existente
    o subir una nueva imagen.
    """
    
    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.attrs.update({
            'class': 'form-control-file',
            'accept': 'image/*'
        })
    
    def format_value(self, value):
        """Format the value for display with safe error handling."""
        return self.safe_format_value(value)
    
    def safe_format_value(self, value):
        """
        Safely format file field value with comprehensive error handling.
        
        Args:
            value: File field value (can be None, empty, or file instance)
            
        Returns:
            str or None: URL of the file, or None if not available
        """
        try:
            # Handle None or empty values
            if not value:
                logger.debug("Widget format_value: value is None or empty")
                return None
                
            # Handle string values (file paths)
            if isinstance(value, str):
                if not value.strip():
                    logger.debug("Widget format_value: string value is empty")
                    return None
                return value
                
            # Handle file field instances
            if hasattr(value, 'url') and hasattr(value, 'name'):
                if not value.name:
                    logger.debug("Widget format_value: file field has no name")
                    return None
                    
                # Use safe utility function
                url = safe_get_image_url(value)
                if url:
                    logger.debug(f"Widget format_value: successfully got URL for {value.name}")
                    return url
                else:
                    logger.debug(f"Widget format_value: could not get URL for {value.name}")
                    return None
                    
            # Handle other types
            logger.debug(f"Widget format_value: unexpected value type {type(value)}")
            return None
            
        except Exception as e:
            log_file_error("widget format_value", value, e, 'warning')
            return None
    
    def safe_render_current_image(self, value):
        """
        Safely render the current image with comprehensive error handling.
        
        Args:
            value: File field value
            
        Returns:
            str: HTML for current image display
        """
        try:
            # Check if value exists and is valid
            if not value:
                return '''
                <div class="current-image mb-3">
                    <label class="form-label">Imagen actual:</label>
                    <div class="alert alert-info" style="padding: 10px; margin: 5px 0;">
                        <i class="fas fa-info-circle"></i> No hay imagen seleccionada
                    </div>
                </div>
                '''
            
            # Get safe URL
            image_url = safe_get_image_url(value)
            
            if image_url:
                # Validate that the image file actually exists
                file_path = getattr(value, 'name', str(value))
                validation = validate_image_file(file_path)
                
                if validation['valid']:
                    return f'''
                    <div class="current-image mb-3">
                        <label class="form-label">Imagen actual:</label>
                        <div class="image-preview">
                            <img src="{image_url}" alt="Imagen actual" 
                                 style="max-width: 200px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;"
                                 onerror="this.parentElement.innerHTML='<div class=\\'alert alert-warning\\'>Error cargando imagen</div>'">
                            <div class="image-info" style="font-size: 0.8em; color: #666; margin-top: 5px;">
                                Archivo: {file_path}
                            </div>
                        </div>
                    </div>
                    '''
                else:
                    # Image reference exists but file is invalid
                    return f'''
                    <div class="current-image mb-3">
                        <label class="form-label">Imagen actual:</label>
                        <div class="alert alert-warning" style="padding: 10px; margin: 5px 0;">
                            <i class="fas fa-exclamation-triangle"></i> 
                            Imagen no válida: {validation['message']}
                            <br><small>Archivo: {file_path}</small>
                            <br><button type="button" class="btn btn-sm btn-outline-danger mt-2" 
                                       onclick="clearInvalidImage()">Limpiar imagen inválida</button>
                        </div>
                    </div>
                    '''
            else:
                # Value exists but URL cannot be obtained
                file_info = getattr(value, 'name', str(value)) if value else 'desconocido'
                return f'''
                <div class="current-image mb-3">
                    <label class="form-label">Imagen actual:</label>
                    <div class="alert alert-warning" style="padding: 10px; margin: 5px 0;">
                        <i class="fas fa-exclamation-triangle"></i> 
                        No se puede acceder a la imagen
                        <br><small>Referencia: {file_info}</small>
                        <br><button type="button" class="btn btn-sm btn-outline-danger mt-2" 
                                   onclick="clearInvalidImage()">Limpiar referencia</button>
                    </div>
                </div>
                '''
                
        except Exception as e:
            log_file_error("widget render_current_image", value, e, 'error')
            return f'''
            <div class="current-image mb-3">
                <label class="form-label">Imagen actual:</label>
                <div class="alert alert-danger" style="padding: 10px; margin: 5px 0;">
                    <i class="fas fa-times-circle"></i> 
                    Error procesando imagen: {str(e)}
                    <br><button type="button" class="btn btn-sm btn-outline-danger mt-2" 
                               onclick="clearInvalidImage()">Limpiar y continuar</button>
                </div>
            </div>
            '''

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget with image selector and safe error handling."""
        try:
            # Get existing images
            existing_images = self.get_existing_images()
            
            # Base file input
            file_input = super().render(name, value, attrs, renderer)
            
            # Current image display with safe rendering
            current_image_html = self.safe_render_current_image(value)
        
            # Image selector HTML with comprehensive error handling
            selector_html = f'''
            <div class="image-selector-widget">
                {current_image_html}
                
                <div class="mb-3">
                    <label class="form-label">Subir nueva imagen:</label>
                    {file_input}
                </div>
                
                <div class="mb-3">
                    <label class="form-label">O seleccionar imagen existente:</label>
                    <div class="existing-images-container">
                        <div class="row" id="existing-images-grid">
                            {self.safe_render_existing_images(existing_images, name)}
                        </div>
                        <!-- Galería de imágenes cargada -->
                    </div>
                </div>
                
                <input type="hidden" id="{name}-selected-image-path" name="{name}_selected" value="">
            </div>
            
            <script>
            function selectExistingImage(imagePath, imageUrl, inputName) {{
                try {{
                    console.log('Seleccionando imagen:', imagePath);
                    
                    // Set the hidden field value
                    const hiddenField = document.getElementById('{name}-selected-image-path');
                    if (hiddenField) {{
                        hiddenField.value = imagePath;
                        console.log('Campo hidden actualizado:', hiddenField.name, '=', hiddenField.value);
                    }} else {{
                        console.error('No se encontró el campo hidden con ID: {name}-selected-image-path');
                    }}
                    
                    // Clear file input
                    const fileInput = document.querySelector('input[name="{name}"]');
                    if (fileInput) {{
                        fileInput.value = '';
                        console.log('Campo de archivo limpiado');
                    }}
                    
                    // Update preview
                    updateImagePreview(imageUrl);
                    
                    // Update selection visual feedback
                    document.querySelectorAll('.existing-image-item').forEach(item => {{
                        item.classList.remove('selected');
                    }});
                    event.target.closest('.existing-image-item').classList.add('selected');
                    
                    console.log('Imagen seleccionada exitosamente');
                }} catch (error) {{
                    console.error('Error selecting image:', error);
                    alert('Error seleccionando la imagen. Por favor, intenta de nuevo.');
                }}
            }}
            
            function updateImagePreview(imageUrl) {{
                try {{
                    let previewContainer = document.querySelector('.current-image');
                    if (!previewContainer) {{
                        previewContainer = document.createElement('div');
                        previewContainer.className = 'current-image mb-3';
                        document.querySelector('.image-selector-widget').insertBefore(
                            previewContainer, 
                            document.querySelector('.image-selector-widget').firstChild
                        );
                    }}
                    
                    previewContainer.innerHTML = `
                        <label class="form-label">Imagen seleccionada:</label>
                        <div class="image-preview">
                            <img src="${{imageUrl}}" alt="Imagen seleccionada" 
                                 style="max-width: 200px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px;"
                                 onerror="this.parentElement.innerHTML='<div class=\\'alert alert-warning\\'>Error cargando imagen seleccionada</div>'">
                        </div>
                    `;
                }} catch (error) {{
                    console.error('Error updating preview:', error);
                }}
            }}
            
            function clearInvalidImage() {{
                try {{
                    // Clear the file input
                    const fileInput = document.querySelector('input[name="{name}"]');
                    if (fileInput) {{
                        fileInput.value = '';
                    }}
                    
                    // Clear the selected image path
                    const selectedPath = document.getElementById('{name}-selected-image-path');
                    if (selectedPath) {{
                        selectedPath.value = '';
                    }}
                    
                    // Update the current image display
                    const currentImageDiv = document.querySelector('.current-image');
                    if (currentImageDiv) {{
                        currentImageDiv.innerHTML = `
                            <label class="form-label">Imagen actual:</label>
                            <div class="alert alert-info" style="padding: 10px; margin: 5px 0;">
                                <i class="fas fa-info-circle"></i> No hay imagen seleccionada
                            </div>
                        `;
                    }}
                    
                    // Remove selection from existing images
                    document.querySelectorAll('.existing-image-item').forEach(item => {{
                        item.classList.remove('selected');
                    }});
                    
                }} catch (error) {{
                    console.error('Error clearing image:', error);
                    alert('Error limpiando la imagen. Por favor, recarga la página.');
                }}
            }}
            
            // Función para debug - no hace peticiones HTTP
            function debugImageSelector() {{
                console.log('Image selector widget loaded successfully');
            }}
            </script>
        
        <style>
        .existing-images-container {{
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background-color: #f8f9fa;
        }}
        
        .existing-image-item {{
            cursor: pointer;
            border: 2px solid transparent;
            border-radius: 4px;
            padding: 5px;
            transition: all 0.2s;
        }}
        
        .existing-image-item:hover {{
            border-color: #007bff;
            background-color: #e3f2fd;
        }}
        
        .existing-image-item.selected {{
            border-color: #28a745;
            background-color: #d4edda;
        }}
        
        .existing-image-item img {{
            width: 100%;
            height: 80px;
            object-fit: cover;
            border-radius: 2px;
        }}
        
        .existing-image-item .image-name {{
            font-size: 0.8em;
            text-align: center;
            margin-top: 5px;
            word-break: break-all;
        }}
        </style>
        '''
        
            return mark_safe(selector_html)
            
        except Exception as e:
            log_file_error("widget render", value, e, 'error')
            # Return a minimal functional widget in case of complete failure
            file_input = super().render(name, value, attrs, renderer)
            error_html = f'''
            <div class="image-selector-widget">
                <div class="alert alert-danger" style="padding: 10px; margin: 10px 0;">
                    <i class="fas fa-exclamation-triangle"></i> 
                    Error cargando el selector de imágenes: {str(e)}
                </div>
                <div class="mb-3">
                    <label class="form-label">Subir imagen:</label>
                    {file_input}
                </div>
            </div>
            '''
            return mark_safe(error_html)
    
    def get_existing_images(self):
        """Get list of existing images from various folders."""
        images = []
        
        # Folders to search for images
        image_folders = [
            'ai_posts/content/',  # Imágenes extraídas del contenido
            'ai_posts/covers/',   # Imágenes de portada generadas (si las hay)
            'post_images/',       # Imágenes subidas manualmente
            'uploads/',           # Otras imágenes subidas
            'images/',            # Carpeta general de imágenes
        ]
        
        for folder in image_folders:
            try:
                if default_storage.exists(folder):
                    # List files in folder
                    _, files = default_storage.listdir(folder)
                    
                    for file in files:
                        if self.is_image_file(file):
                            file_path = os.path.join(folder, file).replace('\\', '/')
                            images.append({
                                'path': file_path,
                                'url': default_storage.url(file_path),
                                'name': file,
                                'folder': folder
                            })
            except Exception as e:
                # Folder doesn't exist or can't be accessed
                continue
        
        # Sort by modification time (newest first) if possible
        return sorted(images, key=lambda x: x['name'], reverse=True)[:20]  # Limit to 20 images
    
    def safe_render_existing_images(self, images, input_name):
        """Safely render the grid of existing images with error handling."""
        try:
            if not images:
                return '''
                <div class="col-12">
                    <div class="alert alert-info" style="padding: 15px; text-align: center;">
                        <i class="fas fa-info-circle"></i> 
                        No hay imágenes disponibles en la galería.
                        <br><small>Genera algunas imágenes usando el generador de IA o sube imágenes manualmente.</small>
                    </div>
                </div>
                '''
            
            html_parts = []
            for image in images:
                try:
                    # Validate image data
                    if not all(key in image for key in ['path', 'url', 'name']):
                        logger.warning(f"Invalid image data structure: {image}")
                        continue
                        
                    # Escape HTML attributes to prevent XSS
                    safe_path = image['path'].replace("'", "\\'").replace('"', '\\"')
                    safe_url = image['url'].replace("'", "\\'").replace('"', '\\"')
                    safe_name = image['name'].replace('<', '&lt;').replace('>', '&gt;')
                    
                    html_parts.append(f'''
                    <div class="col-md-3 col-sm-4 col-6 mb-2">
                        <div class="existing-image-item" onclick="selectExistingImage('{safe_path}', '{safe_url}', '{input_name}')">
                            <img src="{safe_url}" alt="{safe_name}" loading="lazy"
                                 onerror="this.parentElement.innerHTML='<div class=\\'text-danger\\' style=\\'padding:10px;text-align:center;\\'>Error<br>cargando<br>imagen</div>'">
                            <div class="image-name">{safe_name}</div>
                        </div>
                    </div>
                    ''')
                except Exception as e:
                    logger.warning(f"Error rendering image {image}: {e}")
                    # Continue with other images
                    continue
            
            if not html_parts:
                return '''
                <div class="col-12">
                    <div class="alert alert-warning" style="padding: 15px; text-align: center;">
                        <i class="fas fa-exclamation-triangle"></i> 
                        No se pudieron cargar las imágenes de la galería.
                        <br><small>Verifica que las imágenes existan y sean accesibles.</small>
                    </div>
                </div>
                '''
            
            return ''.join(html_parts)
            
        except Exception as e:
            log_file_error("widget render_existing_images", images, e, 'error')
            return '''
            <div class="col-12">
                <div class="alert alert-danger" style="padding: 15px; text-align: center;">
                    <i class="fas fa-times-circle"></i> 
                    Error cargando la galería de imágenes.
                    <br><small>Usa la opción de subir imagen directamente.</small>
                </div>
            </div>
            '''
    
    def render_existing_images(self, images, input_name):
        """Legacy method - redirects to safe version."""
        return self.safe_render_existing_images(images, input_name)
    
    def is_image_file(self, filename):
        """Check if file is an image."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        return any(filename.lower().endswith(ext) for ext in image_extensions)
    
    def value_from_datadict(self, data, files, name):
        """Extract value from form data."""
        # Check if an existing image was selected
        selected_path = data.get(f'{name}_selected')
        
        if selected_path:
            # Return the selected image path as string
            return selected_path
        
        # Otherwise, use the uploaded file
        uploaded_file = super().value_from_datadict(data, files, name)
        return uploaded_file