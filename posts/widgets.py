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
                    <div class="mb-2">
                        <small class="text-muted">
                            <i class="fas fa-clock"></i> Ordenadas por fecha (más recientes primero)
                            {f' • {len(existing_images)} imágenes disponibles' if existing_images else ''}
                        </small>
                    </div>
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
            max-height: 400px;
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
            position: relative;
        }}
        
        .existing-image-item:hover {{
            border-color: #007bff;
            background-color: #e3f2fd;
        }}
        
        .existing-image-item.selected {{
            border-color: #28a745;
            background-color: #d4edda;
        }}
        
        .image-container {{
            position: relative;
            overflow: hidden;
            border-radius: 4px;
        }}
        
        .existing-image-item img {{
            width: 100%;
            height: 100px;
            object-fit: cover;
            border-radius: 2px;
            transition: transform 0.2s;
        }}
        
        .existing-image-item:hover img {{
            transform: scale(1.05);
        }}
        
        .image-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to bottom, rgba(0,0,0,0.7) 0%, transparent 40%, transparent 60%, rgba(0,0,0,0.7) 100%);
            opacity: 0;
            transition: opacity 0.2s;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 5px;
        }}
        
        .existing-image-item:hover .image-overlay {{
            opacity: 1;
        }}
        
        .image-info {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        
        .date-info, .size-info {{
            color: white;
            font-size: 0.7em;
            background: rgba(0,0,0,0.5);
            padding: 2px 4px;
            border-radius: 2px;
            font-weight: 500;
        }}
        
        .existing-image-item .image-name {{
            font-size: 0.75em;
            text-align: center;
            margin-top: 5px;
            word-break: break-all;
            line-height: 1.2;
            max-height: 2.4em;
            overflow: hidden;
            color: #555;
        }}
        
        .existing-image-item:hover .image-name {{
            color: #007bff;
            font-weight: 500;
        }}
        
        .existing-image-item.selected .image-name {{
            color: #28a745;
            font-weight: 600;
        }}
        
        /* Indicador de imagen reciente */
        .existing-image-item[data-recent="true"]::before {{
            content: "Nuevo";
            position: absolute;
            top: 8px;
            right: 8px;
            background: #28a745;
            color: white;
            font-size: 0.6em;
            padding: 2px 4px;
            border-radius: 2px;
            z-index: 10;
            font-weight: 600;
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
        """Get list of existing images from various folders, sorted by creation date (newest first)."""
        images = []
        
        # Folders to search for images
        image_folders = [
            'ai_posts/content/',  # Imágenes extraídas del contenido
            'ai_posts/covers/',   # Imágenes de portada generadas (si las hay)
            'ai_posts/images/',   # Imágenes generadas por IA
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
                            
                            # Get file creation/modification time
                            try:
                                file_stats = default_storage.get_created_time(file_path)
                                modified_time = file_stats.timestamp() if file_stats else 0
                            except Exception:
                                # Fallback to current time if can't get file stats
                                import time
                                modified_time = time.time()
                            
                            # Get file size for additional info
                            try:
                                file_size = default_storage.size(file_path)
                                size_mb = round(file_size / (1024 * 1024), 2)
                            except Exception:
                                file_size = 0
                                size_mb = 0
                            
                            images.append({
                                'path': file_path,
                                'url': default_storage.url(file_path),
                                'name': file,
                                'folder': folder,
                                'modified_time': modified_time,
                                'size_bytes': file_size,
                                'size_mb': size_mb
                            })
            except Exception as e:
                logger.warning(f"Error accessing folder {folder}: {e}")
                continue
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
        
        # Limit to 30 most recent images
        return images[:30]
    
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
                    
                    # Format date and size info
                    date_info = ""
                    size_info = ""
                    
                    if 'modified_time' in image and image['modified_time']:
                        try:
                            from datetime import datetime
                            date_obj = datetime.fromtimestamp(image['modified_time'])
                            date_info = date_obj.strftime('%d/%m/%Y')
                        except Exception:
                            date_info = ""
                    
                    if 'size_mb' in image and image['size_mb']:
                        if image['size_mb'] < 1:
                            size_info = f"{int(image['size_bytes'] / 1024)}KB"
                        else:
                            size_info = f"{image['size_mb']}MB"
                    
                    # Create tooltip with additional info
                    tooltip_info = f"Archivo: {safe_name}"
                    if date_info:
                        tooltip_info += f"\\nFecha: {date_info}"
                    if size_info:
                        tooltip_info += f"\\nTamaño: {size_info}"
                    tooltip_info += f"\\nCarpeta: {image.get('folder', 'N/A')}"
                    
                    # Check if image is recent (last 24 hours)
                    is_recent = False
                    if 'modified_time' in image and image['modified_time']:
                        try:
                            import time
                            current_time = time.time()
                            # 24 hours = 24 * 60 * 60 = 86400 seconds
                            is_recent = (current_time - image['modified_time']) < 86400
                        except Exception:
                            is_recent = False
                    
                    recent_attr = 'data-recent="true"' if is_recent else ''
                    
                    html_parts.append(f'''
                    <div class="col-md-3 col-sm-4 col-6 mb-3">
                        <div class="existing-image-item" {recent_attr} onclick="selectExistingImage('{safe_path}', '{safe_url}', '{input_name}')" 
                             title="{tooltip_info}">
                            <div class="image-container">
                                <img src="{safe_url}" alt="{safe_name}" loading="lazy"
                                     onerror="this.parentElement.innerHTML='<div class=\\'text-danger\\' style=\\'padding:10px;text-align:center;\\'>Error<br>cargando<br>imagen</div>'">
                                <div class="image-overlay">
                                    <div class="image-info">
                                        {f'<small class="date-info">{date_info}</small>' if date_info else ''}
                                        {f'<small class="size-info">{size_info}</small>' if size_info else ''}
                                    </div>
                                </div>
                            </div>
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