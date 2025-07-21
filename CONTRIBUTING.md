# 🤝 Guía de Contribución - DevBlog

¡Gracias por tu interés en contribuir a DevBlog! Esta guía te ayudará a empezar.

## 📋 Tabla de Contenidos

- [🚀 Primeros Pasos](#-primeros-pasos)
- [🔄 Proceso de Contribución](#-proceso-de-contribución)
- [📝 Estándares de Código](#-estándares-de-código)
- [🧪 Testing](#-testing)
- [📖 Documentación](#-documentación)
- [🐛 Reportar Bugs](#-reportar-bugs)
- [💡 Sugerir Features](#-sugerir-features)

## 🚀 Primeros Pasos

### 1. Fork y Clone

```bash
# Fork el repositorio en GitHub, luego:
git clone https://github.com/TU-USERNAME/Project-Final-Informatorio-25.git
cd Project-Final-Informatorio-25
```

### 2. Configurar Entorno de Desarrollo

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Si existe

# Configurar base de datos
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
```

### 3. Verificar Instalación

```bash
# Ejecutar tests
python manage.py test

# Ejecutar servidor
python manage.py runserver
```

## 🔄 Proceso de Contribución

### 1. Crear una Rama

```bash
# Crear rama desde main
git checkout main
git pull origin main
git checkout -b feature/nombre-descriptivo

# Ejemplos de nombres de rama:
# feature/ai-content-generator
# bugfix/like-button-not-working
# docs/update-installation-guide
```

### 2. Hacer Cambios

- Mantén los commits pequeños y enfocados
- Escribe mensajes de commit descriptivos
- Sigue las convenciones de código del proyecto

### 3. Commit y Push

```bash
# Agregar cambios
git add .

# Commit con mensaje descriptivo
git commit -m "feat: add AI content generation feature

- Integrate Google Gemini API
- Add content extraction from URLs
- Implement automatic tag generation
- Add user permission checks"

# Push a tu fork
git push origin feature/nombre-descriptivo
```

### 4. Crear Pull Request

1. Ve a GitHub y crea un Pull Request
2. Usa el template de PR (si existe)
3. Describe claramente los cambios
4. Vincula issues relacionados
5. Espera la revisión

## 📝 Estándares de Código

### Python/Django

```python
# Usar PEP 8
# Líneas máximo 88 caracteres (Black formatter)
# Imports organizados con isort

# Ejemplo de función bien documentada:
def generate_ai_content(url: str, prompt: str) -> dict:
    """
    Generate AI content from URL using Gemini API.
    
    Args:
        url: Source URL to extract content from
        prompt: AI generation prompt
        
    Returns:
        dict: Generated content with title, body, and tags
        
    Raises:
        APIError: If Gemini API request fails
        ValidationError: If URL is invalid
    """
    pass
```

### HTML/CSS

```html
<!-- Usar clases semánticas -->
<article class="post-card glass-effect">
    <header class="post-header">
        <h2 class="post-title">{{ post.title }}</h2>
    </header>
</article>
```

```css
/* Usar nomenclatura BEM cuando sea apropiado */
.post-card {
    /* Propiedades ordenadas alfabéticamente */
    background: rgba(255, 255, 255, 0.1);
    border-radius: 1rem;
    padding: 1.5rem;
}

.post-card__title {
    font-size: 1.5rem;
    font-weight: 600;
}
```

### JavaScript

```javascript
// Usar ES6+ features
// Funciones arrow cuando sea apropiado
// Async/await en lugar de .then()

const handleLikeClick = async (postId) => {
    try {
        const response = await fetch(`/api/posts/${postId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json',
            },
        });
        
        if (!response.ok) {
            throw new Error('Failed to like post');
        }
        
        const data = await response.json();
        updateLikeButton(data);
    } catch (error) {
        console.error('Error liking post:', error);
        showErrorMessage('Error al dar like');
    }
};
```

## 🧪 Testing

### Escribir Tests

```python
# tests.py
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Post

class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
    def test_post_creation(self):
        """Test that post is created correctly"""
        post = Post.objects.create(
            title='Test Post',
            content='Test content',
            author=self.user,
            status='published'
        )
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.user)
        self.assertTrue(post.slug)
```

### Ejecutar Tests

```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test posts.tests.PostModelTest

# Con cobertura
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Cobertura Mínima

- Nuevas funciones: 100% cobertura
- Código existente: No reducir cobertura
- Tests de integración para features complejas

## 📖 Documentación

### Docstrings

```python
def complex_function(param1: str, param2: int = 10) -> dict:
    """
    Brief description of what the function does.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of first parameter
        param2: Description of second parameter with default
        
    Returns:
        dict: Description of return value
        
    Raises:
        ValueError: When param1 is empty
        TypeError: When param2 is not an integer
        
    Example:
        >>> result = complex_function("hello", 5)
        >>> print(result['status'])
        'success'
    """
    pass
```

### Comentarios en Código

```python
# ✅ Bueno: Explica el "por qué"
# Calculate reading time based on average 200 words per minute
reading_time = word_count / 200

# ❌ Malo: Explica el "qué" (obvio)
# Increment the counter by 1
counter += 1
```

### Actualizar Documentación

- Actualiza README.md si cambias funcionalidades principales
- Actualiza docs/ si cambias configuración o instalación
- Agrega ejemplos de uso para nuevas features

## 🐛 Reportar Bugs

### Antes de Reportar

1. Busca en issues existentes
2. Verifica que sea reproducible
3. Prueba en la última versión

### Template de Bug Report

```markdown
**Descripción del Bug**
Descripción clara y concisa del problema.

**Pasos para Reproducir**
1. Ve a '...'
2. Haz click en '....'
3. Scroll hasta '....'
4. Ver error

**Comportamiento Esperado**
Descripción de lo que esperabas que pasara.

**Screenshots**
Si aplica, agrega screenshots.

**Información del Sistema:**
- OS: [e.g. Ubuntu 20.04]
- Python: [e.g. 3.9.7]
- Django: [e.g. 4.2.7]
- Browser: [e.g. Chrome 91.0]

**Contexto Adicional**
Cualquier otra información relevante.
```

## 💡 Sugerir Features

### Template de Feature Request

```markdown
**¿Tu feature request está relacionado con un problema?**
Descripción clara del problema. Ej: "Me frustra que..."

**Describe la solución que te gustaría**
Descripción clara de lo que quieres que pase.

**Describe alternativas que consideraste**
Descripción de soluciones alternativas.

**Contexto adicional**
Screenshots, mockups, o cualquier contexto adicional.
```

## 🏷️ Convenciones de Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Formato
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]

# Ejemplos
feat: add AI content generation
fix: resolve like button not updating count
docs: update installation guide
style: format code with black
refactor: extract user permission logic
test: add tests for post creation
chore: update dependencies
```

### Tipos de Commit

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (no afectan funcionalidad)
- `refactor`: Refactoring de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

## 🎯 Áreas de Contribución

### 🔰 Para Principiantes

- Corregir typos en documentación
- Agregar tests para código existente
- Mejorar mensajes de error
- Agregar validaciones simples

### 🚀 Intermedio

- Implementar nuevas features
- Optimizar consultas de base de datos
- Mejorar UI/UX
- Agregar integraciones con APIs

### 🏆 Avanzado

- Arquitectura y refactoring mayor
- Optimizaciones de rendimiento
- Configuración de CI/CD
- Implementar nuevas tecnologías

## 📞 Contacto

- **Issues**: Para bugs y feature requests
- **Discussions**: Para preguntas generales
- **Email**: [tu-email@ejemplo.com] para temas sensibles

## 🙏 Reconocimientos

Todos los contribuidores serán reconocidos en:
- README.md
- Página de créditos del sitio
- Release notes

¡Gracias por contribuir a DevBlog! 🎉