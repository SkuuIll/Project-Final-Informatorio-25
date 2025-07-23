"""
Gestor de prompts para IA - Permite crear, editar y usar prompts personalizados.
"""

from django.contrib.auth.models import User
from .models import AIPromptTemplate


class PromptManager:
    """Gestor de prompts de IA."""
    
    @staticmethod
    def get_default_prompt(prompt_type: str) -> str:
        """
        Obtiene el prompt por defecto para un tipo específico.
        
        Args:
            prompt_type: Tipo de prompt ('content', 'tags', 'image')
            
        Returns:
            Template del prompt por defecto
        """
        try:
            template = AIPromptTemplate.objects.get(
                prompt_type=prompt_type,
                is_default=True,
                is_active=True
            )
            return template.template
        except AIPromptTemplate.DoesNotExist:
            # Fallback a prompts hardcodeados
            return PromptManager._get_fallback_prompt(prompt_type)
    
    @staticmethod
    def _get_fallback_prompt(prompt_type: str) -> str:
        """Prompts de fallback si no hay templates en la BD."""
        
        if prompt_type == 'content':
            return """Eres un redactor experto especializado en contenido técnico, tecnología y programación. Tu misión es transformar el contenido proporcionado en un artículo excepcional, único y altamente engaging.

## 🎯 OBJETIVO PRINCIPAL
Crear un artículo que no solo informe, sino que inspire, eduque y genere valor real para desarrolladores y profesionales de tecnología.

## 📝 INSTRUCCIONES DETALLADAS

### 1. TÍTULO MAGNÉTICO (Máximo 60 caracteres)
- Debe ser irresistible y generar curiosidad
- Incluye números, beneficios o palabras de poder cuando sea apropiado
- Optimizado para SEO pero priorizando el engagement humano
- Ejemplos de palabras poderosas: "Definitiva", "Secretos", "Revoluciona", "Domina", "Transforma"

### 2. ESTRUCTURA HTML PROFESIONAL

**INTRODUCCIÓN IMPACTANTE (2-3 párrafos):**
```html
<p><strong>Hook inicial</strong> que capture la atención inmediatamente. Plantea un problema, estadística sorprendente o pregunta provocativa.</p>
<p>Desarrolla el contexto y explica por qué este tema es crucial <em>ahora mismo</em> para el lector.</p>
<p>Promesa de valor: qué aprenderá específicamente y cómo le beneficiará.</p>
```

**DESARROLLO CON SUBTÍTULOS ESTRATÉGICOS:**
- `<h2>` para secciones principales (máximo 5 palabras, orientadas a beneficios)
- `<h3>` para subsecciones específicas
- Cada sección debe resolver una pregunta específica del lector

**ELEMENTOS VISUALES Y ENGAGEMENT:**
- `<blockquote><p>"Citas impactantes o estadísticas clave"</p></blockquote>`
- `<ul><li>Listas de beneficios, características o pasos</li></ul>`
- `<ol><li>Procesos paso a paso numerados</li></ol>`
- `<code>código inline</code> para comandos o variables
- `<pre><code>bloques de código completos con ejemplos prácticos</code></pre>`
- `<strong>texto destacado</strong>` para conceptos clave
- `<em>énfasis sutil</em>` para matices importantes

**LLAMADAS A LA ACCIÓN INTEGRADAS:**
- Incluye CTAs sutiles a lo largo del contenido
- Usa frases como "Prueba esto:", "Implementa ahora:", "Tu siguiente paso:"

### 3. ESTILO DE ESCRITURA AVANZADO

**TONO Y PERSONALIDAD:**
- Conversacional pero autoritative
- Usa "tú" para crear conexión personal
- Incluye anécdotas breves cuando sea relevante
- Equilibra lo técnico con lo accesible

**TÉCNICAS DE ENGAGEMENT:**
- Preguntas retóricas estratégicas: "¿Te has preguntado por qué...?"
- Transiciones fluidas entre secciones
- Ejemplos concretos y casos de uso reales
- Analogías para conceptos complejos

**OPTIMIZACIÓN PARA LECTURA:**
- Párrafos de máximo 3-4 líneas
- Frases variadas en longitud para ritmo
- Uso estratégico de espacios en blanco
- Palabras de transición para fluidez

### 4. ELEMENTOS TÉCNICOS AVANZADOS

**INTEGRACIÓN DE ENLACES:**
- Convierte URLs en enlaces descriptivos: `<a href="URL" target="_blank">texto que describe el valor del enlace</a>`
- Prioriza enlaces que agreguen valor real al lector

**SUGERENCIAS DE IMÁGENES ESTRATÉGICAS:**
- `<!-- IMAGEN SUGERIDA: Screenshot del dashboard mostrando métricas clave -->`
- `<!-- IMAGEN SUGERIDA: Diagrama de flujo del proceso de implementación -->`
- `<!-- IMAGEN SUGERIDA: Comparativa visual antes/después -->`

**CONCLUSIÓN PODEROSA:**
- Resumen de puntos clave en formato de lista
- Llamada a la acción clara y específica
- Motivación para la implementación inmediata

### 5. OPTIMIZACIÓN SEO NATURAL
- Usa variaciones naturales de palabras clave
- Incluye términos relacionados semánticamente
- Estructura jerárquica clara con H2/H3
- Meta-información implícita en el contenido

## 📊 FORMATO DE RESPUESTA EXACTO

```
Título Magnético Optimizado
---
<p><strong>Hook impactante aquí.</strong> Contexto que establece la importancia del tema y genera curiosidad inmediata.</p>

<p>Desarrollo del problema o oportunidad. Explica por qué el lector <em>necesita</em> esta información ahora.</p>

<p>Promesa de valor específica: "Al final de este artículo, dominarás [beneficio específico] y podrás [resultado concreto]."</p>

<h2>🚀 Primer Beneficio Principal</h2>

<p>Contenido que desarrolla el primer punto clave con ejemplos prácticos.</p>

<blockquote><p>"Estadística o cita impactante que refuerza el punto"</p></blockquote>

<!-- IMAGEN SUGERIDA: Descripción específica de imagen que agregue valor -->

<h3>Implementación Práctica</h3>

<p>Pasos concretos que el lector puede seguir:</p>

<ol>
<li><strong>Paso 1:</strong> Acción específica con <code>ejemplo de código</code></li>
<li><strong>Paso 2:</strong> Siguiente acción con contexto</li>
<li><strong>Paso 3:</strong> Resultado esperado</li>
</ol>

<h2>💡 Segundo Beneficio Clave</h2>

<p>Continúa desarrollando el contenido con la misma estructura...</p>

<h2>🎯 Conclusión y Próximos Pasos</h2>

<p>Resumen de los puntos más importantes:</p>

<ul>
<li><strong>Punto clave 1:</strong> Beneficio específico logrado</li>
<li><strong>Punto clave 2:</strong> Capacidad desarrollada</li>
<li><strong>Punto clave 3:</strong> Resultado tangible</li>
</ul>

<p><strong>Tu próximo paso:</strong> Implementa [acción específica] hoy mismo y comparte tus resultados.</p>

---TAGS---
tag-principal, tecnologia-especifica, herramienta-clave, beneficio-principal, caso-uso, nivel-dificultad
```

## 📚 CONTENIDO A TRANSFORMAR
{content}

## 🔗 RECURSOS ADICIONALES
{urls}

---

**IMPORTANTE:** Crea contenido que sea tan valioso que el lector lo guarde, comparta y regrese a consultarlo. Cada párrafo debe aportar valor tangible."""
        
        elif prompt_type == 'tags':
            return """Eres un especialista en SEO y categorización de contenido técnico. Analiza el contenido proporcionado y genera tags estratégicos que maximicen la visibilidad y relevancia del artículo.

## 🎯 OBJETIVO
Crear 5-7 tags que capturen la esencia del contenido y mejoren su descubribilidad por la audiencia objetivo.

## 📋 CRITERIOS PARA TAGS EFECTIVOS

### TIPOS DE TAGS A INCLUIR:
1. **Tecnología Principal** (1-2 tags): Lenguaje, framework o herramienta central
2. **Categoría Temática** (1 tag): Área general (desarrollo web, machine learning, devops, etc.)
3. **Nivel/Audiencia** (1 tag): principiante, intermedio, avanzado, tutorial, guía
4. **Caso de Uso** (1-2 tags): Aplicación práctica o problema que resuelve
5. **Herramientas/Conceptos** (1-2 tags): Tecnologías secundarias o conceptos clave

### REGLAS DE FORMATO:
- Solo minúsculas
- Usar guiones para palabras compuestas (ej: "machine-learning", "desarrollo-web")
- Máximo 3 palabras por tag
- Evitar artículos y preposiciones
- Priorizar términos que la gente buscaría

### OPTIMIZACIÓN SEO:
- Incluir términos con volumen de búsqueda medio-alto
- Balancear términos específicos y generales
- Considerar sinónimos y variaciones
- Evitar tags demasiado genéricos o competitivos

## 📊 ANÁLISIS DEL CONTENIDO
{content}

## 🏷️ FORMATO DE RESPUESTA
Devuelve ÚNICAMENTE los tags separados por comas, sin explicaciones adicionales.

**Ejemplo de salida correcta:**
python, django, api-rest, desarrollo-web, tutorial, backend, principiante

**IMPORTANTE:** Los tags deben reflejar tanto el contenido técnico como la intención de búsqueda del usuario objetivo."""
        
        elif prompt_type == 'image':
            return """Crea una imagen de portada profesional y visualmente impactante para un artículo de blog técnico.

## 🎨 ESPECIFICACIONES TÉCNICAS
- **Tema:** {title}
- **Palabras clave:** {keywords}
- **Estilo visual:** {style}
- **Dimensiones:** {size}
- **Formato:** Optimizado para web y redes sociales

## 🎯 DIRECTRICES DE DISEÑO

### COMPOSICIÓN VISUAL:
- Diseño limpio y moderno con jerarquía visual clara
- Uso estratégico del espacio negativo para respirabilidad
- Elementos gráficos que refuercen el tema técnico
- Paleta de colores profesional y coherente

### ELEMENTOS A INCLUIR:
- Iconografía relacionada con tecnología/programación
- Elementos abstractos que representen conceptos técnicos
- Gradientes sutiles o patrones geométricos modernos
- Símbolos universales de la tecnología (código, circuitos, datos, etc.)

### ESTILO SEGÚN CATEGORÍA:
- **Profesional:** Colores corporativos, líneas limpias, minimalismo elegante
- **Moderno:** Gradientes vibrantes, formas geométricas, estética futurista
- **Tecnológico:** Elementos de circuitos, código, interfaces digitales
- **Creativo:** Colores audaces, composiciones dinámicas, elementos artísticos

### ELEMENTOS A EVITAR:
- Texto superpuesto o watermarks
- Imágenes de stock genéricas
- Elementos que distraigan del mensaje principal
- Colores demasiado saturados o contrastantes

## 🚀 PROMPT OPTIMIZADO

Crea una imagen de portada moderna y profesional para un blog de tecnología sobre "{title}". 

La imagen debe transmitir expertise técnico y atraer a desarrolladores y profesionales de tecnología. Incorpora elementos visuales relacionados con {keywords} usando un estilo {style}.

Usa una composición equilibrada con:
- Elementos gráficos que representen conceptos de programación/tecnología
- Paleta de colores profesional que inspire confianza
- Diseño limpio que funcione bien como thumbnail
- Estética moderna que refleje innovación tecnológica

La imagen debe ser visualmente atractiva tanto en tamaño completo como en miniatura, optimizada para {size} y apropiada para compartir en redes sociales profesionales.

**Estilo específico:** {style} - asegúrate de que la imagen refleje esta estética manteniendo la profesionalidad técnica."""
        
        return ""
    
    @staticmethod
    def get_available_prompts(prompt_type: str) -> list:
        """
        Obtiene todos los prompts disponibles para un tipo.
        
        Args:
            prompt_type: Tipo de prompt
            
        Returns:
            Lista de templates disponibles
        """
        return AIPromptTemplate.objects.filter(
            prompt_type=prompt_type,
            is_active=True
        ).order_by('-is_default', 'name')
    
    @staticmethod
    def create_prompt(name: str, prompt_type: str, template: str, user: User, 
                     description: str = "", is_default: bool = False) -> AIPromptTemplate:
        """
        Crea un nuevo template de prompt.
        
        Args:
            name: Nombre del template
            prompt_type: Tipo de prompt
            template: Contenido del template
            user: Usuario que crea el template
            description: Descripción opcional
            is_default: Si debe ser el template por defecto
            
        Returns:
            Template creado
        """
        return AIPromptTemplate.objects.create(
            name=name,
            prompt_type=prompt_type,
            template=template,
            description=description,
            is_default=is_default,
            created_by=user
        )
    
    @staticmethod
    def update_prompt(prompt_id: int, **kwargs) -> AIPromptTemplate:
        """
        Actualiza un template de prompt existente.
        
        Args:
            prompt_id: ID del template
            **kwargs: Campos a actualizar
            
        Returns:
            Template actualizado
        """
        template = AIPromptTemplate.objects.get(id=prompt_id)
        
        for field, value in kwargs.items():
            if hasattr(template, field):
                setattr(template, field, value)
        
        template.save()
        return template
    
    @staticmethod
    def set_default_prompt(prompt_id: int) -> AIPromptTemplate:
        """
        Establece un prompt como por defecto para su tipo.
        
        Args:
            prompt_id: ID del template
            
        Returns:
            Template actualizado
        """
        template = AIPromptTemplate.objects.get(id=prompt_id)
        template.is_default = True
        template.save()  # El modelo se encarga de desactivar otros defaults
        return template
    
    @staticmethod
    def get_prompt_by_id(prompt_id: int) -> AIPromptTemplate:
        """
        Obtiene un prompt por su ID.
        
        Args:
            prompt_id: ID del template
            
        Returns:
            Template encontrado
        """
        return AIPromptTemplate.objects.get(id=prompt_id)
    
    @staticmethod
    def delete_prompt(prompt_id: int) -> bool:
        """
        Elimina un template de prompt.
        
        Args:
            prompt_id: ID del template
            
        Returns:
            True si se eliminó exitosamente
        """
        try:
            template = AIPromptTemplate.objects.get(id=prompt_id)
            # No permitir eliminar el template por defecto si es el único
            if template.is_default:
                other_templates = AIPromptTemplate.objects.filter(
                    prompt_type=template.prompt_type,
                    is_active=True
                ).exclude(id=prompt_id)
                
                if other_templates.exists():
                    # Hacer que otro template sea el por defecto
                    other_templates.first().update(is_default=True)
                else:
                    # No permitir eliminar el último template
                    return False
            
            template.delete()
            return True
        except AIPromptTemplate.DoesNotExist:
            return False


def initialize_default_prompts(user: User):
    """
    Inicializa los prompts por defecto si no existen.
    
    Args:
        user: Usuario que creará los prompts por defecto
    """
    prompt_types = ['content', 'tags', 'image']
    
    for prompt_type in prompt_types:
        # Verificar si ya existe un prompt por defecto
        if not AIPromptTemplate.objects.filter(
            prompt_type=prompt_type,
            is_default=True
        ).exists():
            # Crear prompt por defecto
            template = PromptManager._get_fallback_prompt(prompt_type)
            PromptManager.create_prompt(
                name=f"Prompt por defecto - {prompt_type.title()}",
                prompt_type=prompt_type,
                template=template,
                user=user,
                description=f"Prompt por defecto del sistema para {prompt_type}",
                is_default=True
            )