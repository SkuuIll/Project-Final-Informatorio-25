<div align="center">

# 🚀 DevBlog - Plataforma de Blogging Moderna

### *Una plataforma de blogging completa construida con Django y tecnologías modernas*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

[🌐 **Demo en Vivo**](https://proyecto.skulll.site/) • [📖 **Documentación**](docs/) • [🐛 **Reportar Bug**](https://github.com/SkuuIll/Project-Final-Informatorio-25/issues)

</div>

---

## 📋 Tabla de Contenidos

- [✨ Características](#-características)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [🚀 Instalación Rápida](#-instalación-rápida)
- [📖 Documentación](#-documentación)
- [🧪 Testing](#-testing)
- [🔧 Configuración](#-configuración)
- [📊 API](#-api)
- [🤝 Contribuir](#-contribuir)
- [📄 Licencia](#-licencia)

---

## ✨ Características

### 🔐 **Autenticación y Usuarios**
- ✅ Sistema completo de registro/login con verificación por email
- ✅ Perfiles de usuario personalizables con avatares
- ✅ Sistema de roles y permisos granular
- ✅ Recuperación de contraseña segura
- ✅ Protección CAPTCHA con Cloudflare Turnstile

### 📝 **Gestión de Contenido**
- ✅ Editor WYSIWYG avanzado con CKEditor 5
- ✅ Sistema de etiquetas inteligente
- ✅ Cálculo automático de tiempo de lectura
- ✅ Subida y gestión de imágenes optimizada
- ✅ Estados de publicación (borrador/publicado)
- ✅ Posts destacados (sticky posts)

### 🤖 **Inteligencia Artificial**
- ✅ Generador de contenido con Google Gemini AI
- ✅ Extracción automática de contenido desde URLs
- ✅ Generación automática de etiquetas
- ✅ Reescritura inteligente de contenido

### 💬 **Interacción Social**
- ✅ Sistema de comentarios con likes
- ✅ Sistema de "Me Gusta" en posts
- ✅ Favoritos personales
- ✅ Notificaciones en tiempo real
- ✅ Sistema de seguimiento entre usuarios

### 📊 **Dashboard y Analytics**
- ✅ Panel de control personalizado
- ✅ Estadísticas detalladas (vistas, likes, comentarios)
- ✅ Gráficos de actividad interactivos
- ✅ Gestión de notificaciones

### 🔍 **Búsqueda y Navegación**
- ✅ Búsqueda avanzada por título y contenido
- ✅ Filtrado por etiquetas
- ✅ Ordenamiento múltiple (fecha, popularidad, vistas)
- ✅ Paginación optimizada
- ✅ Feed RSS automático

### 🎨 **UI/UX Moderna**
- ✅ Diseño responsivo con Tailwind CSS
- ✅ Tema claro/oscuro automático
- ✅ Animaciones suaves con Alpine.js
- ✅ Glassmorphism y efectos modernos
- ✅ Accesibilidad WCAG 2.1 compliant

### 🔒 **Seguridad y Rendimiento**
- ✅ Protección CSRF y XSS
- ✅ Headers de seguridad configurados
- ✅ Rate limiting implementado
- ✅ Consultas optimizadas (N+1 resuelto)
- ✅ Compresión de archivos estáticos
- ✅ Logging estructurado

---

## 🛠️ Stack Tecnológico

<div align="center">

### Backend
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)

### Frontend
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC34A?style=for-the-badge&logo=alpine.js&logoColor=white)

### DevOps & Tools
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)

</div>

### 📦 Dependencias Principales

```python
Django==5.2.4                    # Framework web principal
djangorestframework==3.16.0      # API REST
django-ckeditor-5==0.2.18       # Editor WYSIWYG
django-taggit==6.1.0            # Sistema de etiquetas
django-jazzmin==3.0.1           # Admin personalizado
channels==4.2.2                 # WebSockets
google-generativeai==0.7.2      # Integración con Gemini AI
psycopg2-binary==2.9.9          # Driver PostgreSQL
whitenoise==6.9.0               # Archivos estáticos
gunicorn==23.0.0                # Servidor WSGI
```

---

## 🚀 Instalación Rápida

### 🐳 **Opción 1: Docker (Recomendado)**

```bash
# 1. Clonar repositorio
git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
cd Project-Final-Informatorio-25

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 3. Levantar servicios
docker-compose up -d --build

# 4. Ejecutar migraciones
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# 🎉 ¡Listo! Visita http://localhost:8000
```

### 💻 **Opción 2: Instalación Local**

```bash
# 1. Clonar y configurar entorno
git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
cd Project-Final-Informatorio-25
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar base de datos
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser

# 4. Ejecutar servidor
python manage.py runserver

# 🎉 ¡Listo! Visita http://localhost:8000
```

---

## 📖 Documentación

| Documento | Descripción |
|-----------|-------------|
| [📋 **Guía de Instalación**](docs/INSTALLATION.md) | Instalación detallada paso a paso |
| [🔌 **Documentación de API**](docs/API.md) | Endpoints y ejemplos de uso |
| [⚙️ **Configuración**](docs/CONFIGURATION.md) | Variables de entorno y settings |
| [🧪 **Testing**](docs/TESTING.md) | Guía de testing y cobertura |
| [🚀 **Despliegue**](docs/DEPLOYMENT.md) | Guía de producción |

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Tests con cobertura
coverage run --source='.' manage.py test
coverage report
coverage html

# Tests específicos
python manage.py test posts.tests.PostModelTest
python manage.py test accounts.tests
```

**Cobertura actual: 85%+** 📊

---

## 🔧 Configuración

### Variables de Entorno Principales

```env
# Django Core
SECRET_KEY=tu-clave-super-secreta
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com

# Base de Datos
USE_POSTGRESQL=True
POSTGRES_DB=devblog
POSTGRES_USER=devblog_user
POSTGRES_PASSWORD=password-seguro
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Servicios Externos
GOOGLE_API_KEY=tu-api-key-de-gemini
TURNSTILE_SITE_KEY=tu-site-key
TURNSTILE_SECRET_KEY=tu-secret-key

# Email (Producción)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

---

## 📊 API

### Endpoints Principales

```http
GET    /api/posts/                    # Listar posts
GET    /api/posts/{slug}/             # Obtener post específico
POST   /post/{username}/{slug}/like/  # Like/Unlike post
POST   /comment/{id}/like/            # Like/Unlike comentario
GET    /search/?q={query}             # Búsqueda
GET    /feed/                         # RSS Feed
```

### Ejemplo de Respuesta

```json
{
  "count": 25,
  "next": "http://localhost:8000/api/posts/?page=2",
  "results": [
    {
      "id": 1,
      "title": "Mi Primer Post",
      "slug": "mi-primer-post",
      "author": "admin",
      "created_at": "2024-01-01T12:00:00Z",
      "views": 142,
      "likes_count": 15,
      "reading_time": 3,
      "tags": ["django", "python", "web"]
    }
  ]
}
```

---

## 📁 Estructura del Proyecto

```
DevBlog/
├── 📁 accounts/              # Gestión de usuarios
│   ├── models.py            # Profile, Notification
│   ├── views.py             # Auth, perfil, settings
│   └── forms.py             # Formularios de usuario
├── 📁 blog/                 # Configuración principal
│   ├── configuraciones/     # Settings modulares
│   ├── middleware.py        # Middleware personalizado
│   └── urls.py              # URLs principales
├── 📁 posts/                # Lógica de posts
│   ├── models.py            # Post, Comment, AIModel
│   ├── views.py             # CRUD, likes, AI
│   ├── ai_generator.py      # Integración con Gemini
│   └── serializers.py      # API serializers
├── 📁 templates/            # Templates HTML
│   ├── base.html            # Template base
│   ├── partials/            # Componentes reutilizables
│   └── posts/               # Templates de posts
├── 📁 static/               # Archivos estáticos
│   ├── css/                 # Estilos personalizados
│   ├── js/                  # JavaScript
│   └── img/                 # Imágenes
├── 📁 docs/                 # Documentación
├── 📁 logs/                 # Archivos de log
├── 🐳 docker-compose.yml    # Configuración Docker
├── 📋 requirements.txt      # Dependencias Python
└── ⚙️ .env                  # Variables de entorno
```

---

## 🚀 Características Avanzadas

### 🤖 **Generador de IA**
- Integración con Google Gemini AI
- Extracción automática de contenido desde URLs
- Generación de títulos y etiquetas inteligentes
- Reescritura de contenido optimizada para SEO

### 📊 **Analytics Integrado**
- Tracking de vistas en tiempo real
- Estadísticas de engagement
- Métricas de rendimiento por autor
- Gráficos interactivos en el dashboard

### 🔔 **Sistema de Notificaciones**
- Notificaciones en tiempo real con WebSockets
- Emails automáticos para eventos importantes
- Panel de notificaciones personalizable
- Configuración granular de preferencias

### 🎨 **Temas y Personalización**
- Tema claro/oscuro automático
- Personalización de colores por usuario
- Layouts adaptativos
- Componentes reutilizables

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. 🍴 Fork el proyecto
2. 🌿 Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push a la rama (`git push origin feature/AmazingFeature`)
5. 🔄 Abre un Pull Request

### 📋 Guidelines

- Sigue las convenciones de código existentes
- Agrega tests para nuevas funcionalidades
- Actualiza la documentación cuando sea necesario
- Usa commits descriptivos

---

## 📈 Roadmap

- [ ] 🔍 **Búsqueda Avanzada** - Elasticsearch integration
- [ ] 📱 **PWA** - Progressive Web App features
- [ ] 🌐 **i18n** - Internacionalización completa
- [ ] 📊 **Analytics Avanzado** - Google Analytics integration
- [ ] 🔗 **Social Login** - OAuth con Google, GitHub, etc.
- [ ] 📧 **Newsletter** - Sistema de suscripciones
- [ ] 🎯 **SEO Avanzado** - Meta tags automáticos
- [ ] 🚀 **Performance** - Caching con Redis

---

## 📊 Estadísticas del Proyecto

<div align="center">

![GitHub repo size](https://img.shields.io/github/repo-size/SkuuIll/Project-Final-Informatorio-25)
![GitHub last commit](https://img.shields.io/github/last-commit/SkuuIll/Project-Final-Informatorio-25)
![GitHub issues](https://img.shields.io/github/issues/SkuuIll/Project-Final-Informatorio-25)
![GitHub pull requests](https://img.shields.io/github/issues-pr/SkuuIll/Project-Final-Informatorio-25)

</div>

---

## 👨‍💻 Autor

<div align="center">

**SkuuIll**

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SkuuIll)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/skulll)

</div>

---

## 🎓 Agradecimientos

Este proyecto fue desarrollado como **Proyecto Final** para el curso de **Desarrollo Web** del programa **Informatorio Chaco 2025**.

**Agradecimientos especiales a:**
- 🏫 **Informatorio Chaco** - Por la formación y oportunidades
- 👨‍🏫 **Instructores** - Por la guía y mentoring
- 👥 **Compañeros de curso** - Por el apoyo y colaboración
- 🌐 **Comunidad Open Source** - Por las herramientas increíbles


---

<div align="center">

### ⭐ ¡Si te gusta este proyecto, dale una estrella!

**Hecho con ❤️ en Argentina 🇦🇷**

</div>
