from django import forms
from .models import Post, Comment, AIModel, AIPromptTemplate
from django_ckeditor_5.widgets import CKEditor5Widget
from .image_services import registry
from .prompt_manager import PromptManager


class TagWidget(forms.TextInput):
    """Widget personalizado para manejar tags correctamente."""
    
    def format_value(self, value):
        """Convierte los tags a string separado por comas."""
        if value is not None and not isinstance(value, str):
            # Si value es un queryset o lista de objetos Tag
            if hasattr(value, 'all'):
                # Es un manager de tags
                return ', '.join(tag.name for tag in value.all())
            elif hasattr(value, '__iter__'):
                # Es una lista/queryset
                return ', '.join(str(tag) if hasattr(tag, 'name') else str(tag) for tag in value)
        return value if value is not None else ''


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'header_image', 'content', 'tags', 'status']
        widgets = {
            'content': CKEditor5Widget(),
            'tags': TagWidget(attrs={
                'class': 'w-full px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-600 bg-white/50 dark:bg-slate-900/50 text-slate-900 dark:text-slate-100 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 dark:focus:ring-indigo-800 transition-all duration-300 placeholder-slate-400 dark:placeholder-slate-500',
                'placeholder': 'tecnología, web...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si estamos editando un post existente, formatear los tags correctamente
        if self.instance and self.instance.pk:
            # Obtener los nombres de los tags como string
            tag_names = [tag.name for tag in self.instance.tags.all()]
            self.initial['tags'] = ', '.join(tag_names)

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

**FORMATO DE RESPUESTA:**
Título SEO Optimizado
---
<p>Contenido HTML completo aquí...</p>
<h2>Primer Subtítulo</h2>
<p>Más contenido...</p>
<!-- IMAGEN SUGERIDA: Captura de pantalla mostrando la interfaz de la herramienta -->
<p>Continúa el contenido...</p>

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
    

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Obtener prompts disponibles dinámicamente
        content_prompts = PromptManager.get_available_prompts('content')
        tag_prompts = PromptManager.get_available_prompts('tags')
        
        # Crear choices para prompts de contenido
        content_choices = []
        for prompt in content_prompts:
            label = f"{prompt.name}"
            if prompt.is_default:
                label += " (Por defecto)"
            content_choices.append((prompt.id, label))
        
        # Crear choices para prompts de tags
        tag_choices = []
        for prompt in tag_prompts:
            label = f"{prompt.name}"
            if prompt.is_default:
                label += " (Por defecto)"
            tag_choices.append((prompt.id, label))
        
        # Agregar campos de selección de prompts
        if content_choices:
            default_content = next((p.id for p in content_prompts if p.is_default), content_choices[0][0])
            self.fields['content_prompt_template'] = forms.ChoiceField(
                label="Template de prompt para contenido",
                choices=content_choices,
                initial=default_content,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        
        if tag_choices:
            default_tag = next((p.id for p in tag_prompts if p.is_default), tag_choices[0][0])
            self.fields['tag_prompt_template'] = forms.ChoiceField(
                label="Template de prompt para tags",
                choices=tag_choices,
                initial=default_tag,
                required=False,
                widget=forms.Select(attrs={'class': 'form-control'})
            )
        

    
    def clean(self):
        cleaned_data = super().clean()
        # Ya no necesitamos validación especial, el comportamiento es automático
        return cleaned_data


class AIPromptTemplateForm(forms.ModelForm):
    """Formulario para crear/editar templates de prompts."""
    
    class Meta:
        model = AIPromptTemplate
        fields = ['name', 'prompt_type', 'template', 'description', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'prompt_type': forms.Select(attrs={'class': 'form-control'}),
            'template': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Agregar ayuda contextual
        self.fields['template'].help_text = """
        Variables disponibles según el tipo:
        • Contenido: {content}, {urls}
        • Tags: {content}
        • Imagen: {title}, {keywords}, {style}, {size}
        """
        
        self.fields['is_default'].help_text = "Si se marca, este será el prompt por defecto para su tipo"


class PromptPreviewForm(forms.Form):
    """Formulario para previsualizar prompts con datos de prueba."""
    
    template = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
        label="Template del Prompt"
    )
    
    # Campos de prueba
    test_content = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        label="Contenido de prueba",
        required=False,
        initial="Este es un artículo sobre inteligencia artificial y machine learning..."
    )
    
    test_title = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Título de prueba",
        required=False,
        initial="Introducción a la Inteligencia Artificial"
    )
    
    test_keywords = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="Keywords de prueba",
        required=False,
        initial="inteligencia artificial, machine learning, tecnología"
    )