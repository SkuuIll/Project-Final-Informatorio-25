from django import forms
from .models import Post, Comment, AIModel
from django_ckeditor_5.widgets import CKEditor5Widget
from .image_generation import registry

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'header_image', 'content', 'tags', 'status']
        widgets = {
            'content': CKEditor5Widget(),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
        }

class AIModelForm(forms.ModelForm):
    class Meta:
        model = AIModel
        fields = ['name', 'is_active']

REWRITE_PROMPT_DEFAULT = """Eres un asistente de redacción experto para un blog de tecnología y programación.
Tu tarea es reescribir el siguiente texto para que sea único, atractivo y bien estructurado con formato HTML para CKEditor.

**Instrucciones:**
1. **Título:** Crea un título corto, llamativo y optimizado para motores de búsqueda.

2. **Contenido HTML:** Reescribe el texto manteniendo las ideas principales pero con un estilo fresco. 
   Usa el siguiente formato HTML:
   - Párrafos separados con <p></p>
   - Títulos secundarios con <h2></h2> y <h3></h3>
   - Texto en negrita con <strong></strong>
   - Listas ordenadas con <ol><li></li></ol>
   - Listas no ordenadas con <ul><li></li></ul>
   - Enlaces con <a href="URL" target="_blank">texto del enlace</a>
   - Código inline con <code></code>
   - Bloques de código con <pre><code>código aquí</code></pre>
   - Citas con <blockquote><p>texto de la cita</p></blockquote>

3. **Enlaces:** Si encuentras URLs en el texto original, conviértelas en enlaces HTML clickeables.

4. **Estructura:** Organiza el contenido con:
   - Introducción atractiva
   - Subtítulos descriptivos
   - Párrafos cortos (máximo 3-4 líneas)
   - Conclusión o llamada a la acción

5. **Formato de Salida:** Responde únicamente con el título y el contenido HTML, separados por "---".
   
**Ejemplo:**
Cómo la IA Revoluciona la Restauración de Fotos Familiares
---
<p>¿Tienes fotos familiares antiguas llenas de historia pero dañadas por el tiempo? <strong>La inteligencia artificial ha revolucionado</strong> la restauración de imágenes, permitiéndote recuperar esos recuerdos preciados desde casa.</p>

<h2>Olvida los Métodos Tradicionales</h2>
<p>Los métodos tradicionales de restauración eran:</p>
<ul>
<li>Costosos y lentos</li>
<li>Requerían habilidades profesionales</li>
<li>No garantizaban buenos resultados</li>
</ul>

<h2>Herramientas de IA Disponibles</h2>
<p>Existen <strong>numerosas aplicaciones y programas online</strong> que utilizan IA para la restauración:</p>
<ol>
<li><strong>Opciones gratuitas:</strong> Interfaces simples de arrastrar y soltar</li>
<li><strong>Herramientas avanzadas:</strong> Con control manual sobre el proceso</li>
</ol>

**Texto Original:**
{content}
"""

TAG_PROMPT_DEFAULT = """Basado en el siguiente contenido de un artículo, genera una lista de 5 a 7 tags o palabras clave relevantes.
Los tags deben ser cortos, en minúsculas y relevantes para SEO.
Devuelve los tags separados por comas.

**Contenido:**
{content}

**Ejemplo de Salida:**
python, django, desarrollo web, inteligencia artificial, api, tutorial
"""

COMPLETE_POST_PROMPT = """Eres un redactor experto de contenido técnico y de tecnología. Tu tarea es crear un artículo completo y único basado en el contenido proporcionado.

**Instrucciones Específicas:**

1. **TÍTULO SEO:** Crea un título atractivo, optimizado para SEO (máximo 60 caracteres)

2. **CONTENIDO HTML ESTRUCTURADO:**
   Reescribe completamente el contenido usando HTML válido para CKEditor:
   
   - **Introducción atractiva:** 1-2 párrafos con <p></p> que enganchen al lector
   - **Estructura con subtítulos:** Usa <h2></h2> para secciones principales y <h3></h3> para subsecciones
   - **Párrafos cortos:** Máximo 3-4 líneas por párrafo con <p></p>
   - **Elementos visuales:**
     * Listas con <ul><li></li></ul> o <ol><li></li></ol>
     * Texto destacado con <strong></strong>
     * Citas importantes con <blockquote><p></p></blockquote>
     * Código con <code></code> o <pre><code></code></pre>
   - **Enlaces:** Convierte URLs en <a href="URL" target="_blank">texto descriptivo</a>
   - **Conclusión:** Párrafo final con llamada a la acción o resumen

3. **ESTILO DE ESCRITURA:**
   - Usa segunda persona (tú, tu, tus) para conectar con el lector
   - Incluye preguntas retóricas para generar engagement
   - Añade ejemplos prácticos y casos de uso
   - Mantén un tono profesional pero accesible

4. **IMÁGENES Y ENLACES:**
   - Si encuentras enlaces útiles en el contenido original, incorpóralos como enlaces HTML
   - Sugiere dónde podrían ir imágenes usando comentarios HTML: <!-- IMAGEN SUGERIDA: descripción -->

5. **TAGS AUTOMÁTICOS:** Al final del contenido, después de "---TAGS---", proporciona 5-7 tags separados por comas

**FORMATO DE RESPUESTA:**
Título SEO Optimizado
---
<p>Contenido HTML completo aquí...</p>
<h2>Primer Subtítulo</h2>
<p>Más contenido...</p>
<!-- IMAGEN SUGERIDA: Captura de pantalla mostrando la interfaz de la herramienta -->
<p>Continúa el contenido...</p>
---TAGS---
tag1, tag2, tag3, tag4, tag5

**CONTENIDO ORIGINAL A REESCRIBIR:**
{content}

**URLS ENCONTRADAS (si las hay):**
{urls}
"""

class AiPostGeneratorForm(forms.Form):
    url = forms.URLField(
        label="URL del Artículo Original",
        required=True,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    
    prompt_type = forms.ChoiceField(
        label="Tipo de Prompt",
        choices=[
            ('simple', 'Reescritura Simple'),
            ('complete', 'Post Completo con HTML'),
        ],
        initial='complete',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    rewrite_prompt = forms.CharField(
        label="Prompt para Reescribir Contenido",
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 20}),
        initial=COMPLETE_POST_PROMPT
    )
    
    tag_prompt = forms.CharField(
        label="Prompt para Generar Tags",
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        initial=TAG_PROMPT_DEFAULT
    )
    
    # Opciones de Imágenes (sección existente)
    extract_images = forms.BooleanField(
        label="Extraer y procesar imágenes encontradas",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    max_images = forms.IntegerField(
        label="Número máximo de imágenes a extraer",
        required=False,
        initial=5,
        min_value=1,
        max_value=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    # Nuevas opciones para generación de imagen de portada
    generate_cover_image = forms.BooleanField(
        label="Generar imagen de portada automáticamente",
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener servicios disponibles dinámicamente
        available_services = registry.get_available_services()
        service_choices = []
        
        if available_services:
            for service_name in available_services:
                service = registry.get_service(service_name)
                if service:
                    service_choices.append((service_name, service.get_service_name()))
        
        # Si no hay servicios disponibles, mostrar mensaje
        if not service_choices:
            service_choices = [('none', 'No hay servicios disponibles')]
        
        # Agregar campo de servicio de imagen dinámicamente
        self.fields['image_service'] = forms.ChoiceField(
            label="Servicio de generación de imágenes",
            choices=service_choices,
            required=False,
            initial=service_choices[0][0] if service_choices else 'none',
            widget=forms.Select(attrs={'class': 'form-control'})
        )
        
        # Campo de estilo de imagen
        self.fields['image_style'] = forms.ChoiceField(
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
        
        # Campo de tamaño de imagen (si hay servicios disponibles)
        if available_services:
            # Obtener tamaños soportados del primer servicio disponible
            first_service = registry.get_service(available_services[0])
            if first_service:
                supported_params = first_service.get_supported_parameters()
                size_options = supported_params.get('size', {}).get('options', ['1024x1024'])
                
                size_choices = [(size, size) for size in size_options]
                
                self.fields['image_size'] = forms.ChoiceField(
                    label="Tamaño de imagen",
                    choices=size_choices,
                    initial=size_choices[0][0] if size_choices else '1024x1024',
                    required=False,
                    widget=forms.Select(attrs={'class': 'form-control'})
                )
    
    def clean(self):
        cleaned_data = super().clean()
        generate_cover = cleaned_data.get('generate_cover_image')
        image_service = cleaned_data.get('image_service')
        
        # Validar que si se quiere generar imagen, hay un servicio disponible
        if generate_cover and image_service == 'none':
            raise forms.ValidationError(
                "No se puede generar imagen de portada: no hay servicios de generación disponibles. "
                "Configura al menos un servicio (Gemini, OpenAI, etc.) en las variables de entorno."
            )
        
        return cleaned_data