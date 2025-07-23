# Design Document

## Overview

Este diseño extiende el sistema existente de generación de posts con IA para incluir la generación automática de imágenes de portada. El sistema actual ya maneja la extracción de contenido, reescritura con IA, y extracción de imágenes del contenido. Agregaremos la capacidad de generar imágenes de portada únicas usando servicios de IA de generación de imágenes.

La solución se integrará seamlessly con el flujo existente, manteniendo la compatibilidad hacia atrás y agregando nuevas capacidades de configuración.

## Architecture

### Current System Components
- `ai_generator.py`: Módulo principal con funciones de procesamiento de IA
- `AiPostGeneratorForm`: Formulario para configurar la generación
- `generate_complete_post()`: Función principal que orquesta el proceso
- `Post` model con campo `header_image` existente

### New Components
- `ImageGenerationService`: Servicio abstracto para generación de imágenes
- `OpenAIImageGenerator`: Implementación específica para DALL-E
- `StabilityAIGenerator`: Implementación alternativa para Stability AI
- `CoverImagePromptBuilder`: Constructor de prompts optimizados para imágenes
- `ImagePostProcessor`: Procesador para redimensionar y optimizar imágenes

### Integration Points
- Extensión del formulario `AiPostGeneratorForm` con opciones de imagen
- Modificación de `generate_complete_post()` para incluir generación de imagen
- Nuevas configuraciones en variables de entorno
- Actualización de templates para mostrar progreso

## Components and Interfaces

### 1. ImageGenerationService (Abstract Base Class)

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class ImageGenerationService(ABC):
    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Genera una imagen basada en el prompt y retorna la URL local.
        
        Args:
            prompt: Descripción de la imagen a generar
            **kwargs: Parámetros específicos del servicio
            
        Returns:
            URL local de la imagen generada o None si falla
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica si el servicio está disponible y configurado."""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Retorna el nombre del servicio."""
        pass
```

### 2. OpenAIImageGenerator

```python
class OpenAIImageGenerator(ImageGenerationService):
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_IMAGE_MODEL', 'dall-e-3')
        self.size = os.getenv('OPENAI_IMAGE_SIZE', '1792x1024')
        self.quality = os.getenv('OPENAI_IMAGE_QUALITY', 'standard')
    
    def generate_image(self, prompt: str, **kwargs) -> Optional[str]:
        # Implementación usando OpenAI API
        pass
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def get_service_name(self) -> str:
        return "OpenAI DALL-E"
```

### 3. CoverImagePromptBuilder

```python
class CoverImagePromptBuilder:
    @staticmethod
    def build_cover_prompt(title: str, content: str, tags: list = None) -> str:
        """
        Construye un prompt optimizado para generar imagen de portada.
        
        Args:
            title: Título del post
            content: Contenido del post (se extraerán keywords)
            tags: Tags del post (opcional)
            
        Returns:
            Prompt optimizado para generación de imagen
        """
        pass
    
    @staticmethod
    def extract_keywords(content: str, max_keywords: int = 5) -> list:
        """Extrae palabras clave relevantes del contenido."""
        pass
    
    @staticmethod
    def get_style_prompt() -> str:
        """Retorna el estilo visual base para todas las imágenes."""
        pass
```

### 4. Enhanced AiPostGeneratorForm

```python
class AiPostGeneratorForm(forms.Form):
    # Campos existentes...
    
    # Nuevos campos para generación de imagen
    generate_cover_image = forms.BooleanField(
        label="Generar imagen de portada automáticamente",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    image_service = forms.ChoiceField(
        label="Servicio de generación de imágenes",
        choices=[],  # Se populará dinámicamente
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    image_style = forms.ChoiceField(
        label="Estilo de imagen",
        choices=[
            ('professional', 'Profesional/Corporativo'),
            ('modern', 'Moderno/Minimalista'),
            ('tech', 'Tecnológico/Futurista'),
            ('creative', 'Creativo/Artístico'),
        ],
        initial='professional',
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
```

### 5. Enhanced generate_complete_post Function

```python
def generate_complete_post(
    url: str, 
    rewrite_prompt: str, 
    extract_images: bool = True, 
    max_images: int = 5,
    generate_cover: bool = True,
    image_service: str = 'openai',
    image_style: str = 'professional'
) -> dict:
    """
    Función principal mejorada que incluye generación de imagen de portada.
    """
    # Proceso existente...
    
    # Nueva funcionalidad de imagen de portada
    cover_image_url = None
    if generate_cover:
        cover_image_url = generate_cover_image(
            title=ai_result['title'],
            content=ai_result['content'],
            tags=ai_result['tags'],
            service=image_service,
            style=image_style
        )
    
    return {
        'success': True,
        'title': ai_result['title'],
        'content': final_content,
        'tags': ai_result['tags'],
        'cover_image_url': cover_image_url,
        # ... resto de campos existentes
    }
```

## Data Models

### Environment Variables (New)

```bash
# Image Generation Services
OPENAI_API_KEY=your-openai-api-key
OPENAI_IMAGE_MODEL=dall-e-3
OPENAI_IMAGE_SIZE=1792x1024
OPENAI_IMAGE_QUALITY=standard

# Alternative: Stability AI
STABILITY_API_KEY=your-stability-api-key
STABILITY_MODEL=stable-diffusion-xl-1024-v1-0

# Image Generation Settings
DEFAULT_IMAGE_SERVICE=openai
COVER_IMAGE_FOLDER=ai_posts/covers/
MAX_IMAGE_SIZE_MB=5
```

### Database Changes

No se requieren cambios en la base de datos ya que el modelo `Post` ya tiene el campo `header_image`.

### File Structure

```
posts/
├── ai_generator.py (existing, to be extended)
├── image_generation/
│   ├── __init__.py
│   ├── base.py (ImageGenerationService)
│   ├── openai_generator.py
│   ├── stability_generator.py
│   └── prompt_builder.py
├── forms.py (to be extended)
└── views.py (to be extended)
```

## Error Handling

### Image Generation Failures

1. **Service Unavailable**: Si el servicio de imágenes no está disponible, continuar sin imagen
2. **API Errors**: Registrar errores específicos y mostrar mensaje amigable al usuario
3. **Image Processing Errors**: Si falla el procesamiento de imagen, continuar con el post
4. **Storage Errors**: Si falla el guardado, intentar con nombre alternativo

### Fallback Strategy

```python
def generate_cover_image_with_fallback(title: str, content: str, **kwargs) -> Optional[str]:
    """
    Intenta generar imagen con servicio primario, luego fallback.
    """
    services = get_available_image_services()
    
    for service in services:
        try:
            result = service.generate_image(prompt, **kwargs)
            if result:
                return result
        except Exception as e:
            logger.warning(f"Image service {service.get_service_name()} failed: {e}")
            continue
    
    logger.error("All image generation services failed")
    return None
```

## Testing Strategy

### Unit Tests

1. **ImageGenerationService Tests**
   - Test abstract interface compliance
   - Mock API responses
   - Test error handling

2. **CoverImagePromptBuilder Tests**
   - Test keyword extraction
   - Test prompt construction
   - Test different content types

3. **Form Validation Tests**
   - Test new form fields
   - Test service availability checks
   - Test configuration validation

### Integration Tests

1. **End-to-End Post Generation**
   - Test complete flow with image generation
   - Test fallback scenarios
   - Test different image services

2. **API Integration Tests**
   - Test actual API calls (with test keys)
   - Test rate limiting handling
   - Test response parsing

### Performance Tests

1. **Image Generation Performance**
   - Measure generation time
   - Test concurrent requests
   - Test memory usage

2. **Storage Performance**
   - Test image upload speed
   - Test storage space usage
   - Test cleanup processes

## Security Considerations

### API Key Management
- Store API keys in environment variables
- Never log API keys
- Implement key rotation support

### Image Content Validation
- Validate generated images for appropriate content
- Implement content filtering if needed
- Store generation prompts for audit

### Rate Limiting
- Implement rate limiting for image generation
- Cache generated images when possible
- Implement usage tracking

### File Security
- Validate image file types
- Scan for malicious content
- Implement file size limits

## Performance Optimizations

### Asynchronous Processing
- Generate image in background task
- Show progress indicators to user
- Allow post creation without waiting for image

### Caching Strategy
- Cache generated images by prompt hash
- Implement prompt similarity matching
- Cache service availability status

### Resource Management
- Implement cleanup for failed generations
- Monitor storage usage
- Implement automatic cleanup of old images

## User Experience Enhancements

### Progress Indicators
- Show step-by-step progress
- Estimated time remaining
- Cancel operation support

### Preview System
- Show generated image preview
- Allow regeneration with different styles
- Allow manual image upload as alternative

### Configuration UI
- Service status indicators
- Usage statistics
- Error history and diagnostics