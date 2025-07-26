<div align="center">

# 🚀 DevBlog - Plataforma de Blogging con IA

### *Una plataforma de blogging moderna con generación de contenido por IA construida con Django*

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2+-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[🌐 **Demo en Vivo**](https://proyecto.skulll.site/) • [🐛 **Reportar Bug**](https://github.com/SkuuIll/Project-Final-Informatorio-25/issues)

</div>

---

## 📋 Tabla de Contenidos

- [✨ Características](#-características)
- [🛠️ Stack Tecnológico](#️-stack-tecnológico)
- [🚀 Instalación](#-instalación)
- [🔧 Configuración](#-configuración)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [🤖 Generador de IA](#-generador-de-ia)
- [👨‍💻 Autor](#-autor)

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
- ✅ Widget personalizado para selección de imágenes de cabecera
- ✅ Galería de imágenes extraídas automáticamente
- ✅ Estados de publicación (borrador/publicado)
- ✅ Posts destacados (sticky posts)
- ✅ Gestión segura de archivos con validación

### 🤖 **Inteligencia Artificial**
- ✅ Generador de contenido con Google Gemini 2.5-pro
- ✅ Extracción automática de contenido desde URLs
- ✅ Extracción y procesamiento automático de imágenes
- ✅ Generación automática de etiquetas
- ✅ Reescritura inteligente de contenido con formato HTML
- ✅ Selector inteligente de imágenes de cabecera desde medios existentes

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

## 🚀 Instalación

### 📋 **Requisitos Previos**
- **Opción 1 (Docker)**: Docker y Docker Compose
- **Opción 2 (Local)**: Python 3.12+, pip, Git

### 🐳 **Opción 1: Docker (Recomendado para Producción)**

```bash
# 1. Clonar el repositorio
git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
cd Project-Final-Informatorio-25

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 3. Construir y levantar servicios
docker-compose up -d --build

# 4. El sistema estará disponible en:
# - Aplicación: http://localhost:8000
# - Admin: http://localhost:8000/admin (admin/admin123)
# - Flower (Monitor Celery): http://localhost:5555
```

### 🛠️ **Desarrollo con Docker**

```bash
# Para desarrollo (con hot reload)
docker-compose -f docker-compose.dev.yml up --build

# Ver logs
docker-compose logs -f web

# Ejecutar comandos Django
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py shell

# Parar servicios
docker-compose down
```

### 💻 **Opción 2: Instalación Local**

```bash
# 1. Clonar el repositorio
git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
cd Project-Final-Informatorio-25

# 2. Crear y activar entorno virtual
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# 5. Ejecutar migraciones
python manage.py migrate

# 6. Crear superusuario
python manage.py createsuperuser

# 7. Ejecutar servidor de desarrollo
python manage.py runserver

# 🎉 ¡Listo! Visita http://localhost:8000
```

### 🔑 **Acceso por Defecto**
- **Aplicación**: `http://localhost:8000`
- **Admin**: `http://localhost:8000/admin/`
- **Docker**: admin/admin123 (creado automáticamente)
- **Local**: Usa las credenciales del superusuario que creaste

---

## 🔧 Configuración

### Variables de Entorno Principales

```env
# Django Core
SECRET_KEY=tu-clave-super-secreta-aqui
DEBUG=True  # False en producción
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de Datos
USE_POSTGRESQL=False  # True para Docker/Producción
POSTGRES_DB=devblog
POSTGRES_USER=devblog_user
POSTGRES_PASSWORD=devblog_password
POSTGRES_HOST=localhost  # 'db' para Docker
POSTGRES_PORT=5432

# Redis (para Docker/Producción)
REDIS_URL=redis://localhost:6379/0  # redis://redis:6379/0 para Docker

# Servicios de IA
GOOGLE_API_KEY=tu-api-key-de-gemini-aqui

# Seguridad (Opcional)
TURNSTILE_SITE_KEY=tu-site-key
TURNSTILE_SECRET_KEY=tu-secret-key

# Email (Opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password
```

### 🐳 **Configuración para Docker**

Para usar Docker, asegúrate de configurar:
```env
USE_POSTGRESQL=True
POSTGRES_HOST=db
REDIS_URL=redis://redis:6379/0
DEBUG=False  # Para producción
```

### 🔑 **Obtener API Key de Google Gemini**

1. Ve a [Google AI Studio](https://aistudio.google.com/)
2. Inicia sesión con tu cuenta de Google
3. Crea un nuevo proyecto o selecciona uno existente
4. Ve a "Get API Key" y genera una nueva clave
5. Copia la clave y pégala en tu archivo `.env`

---

## 📁 Estructura del Proyecto

```
DevBlog/
├── 📁 accounts/              # Gestión de usuarios y autenticación
│   ├── models.py            # Profile, Notification
│   ├── views.py             # Auth, perfil, configuraciones
│   ├── forms.py             # Formularios de usuario
│   └── admin.py             # Admin personalizado
├── 📁 blog/                 # Configuración principal del proyecto
│   ├── configuraciones/     # Settings modulares
│   │   ├── settings.py      # Configuración principal
│   │   ├── development.py   # Settings de desarrollo
│   │   └── production.py    # Settings de producción
│   ├── middleware.py        # Middleware personalizado
│   ├── urls.py              # URLs principales
│   └── wsgi.py              # Configuración WSGI
├── 📁 posts/                # Lógica principal de posts y contenido
│   ├── models.py            # Post, Comment, AIModel, AIPromptTemplate
│   ├── views.py             # CRUD, likes, búsqueda, AI
│   ├── admin.py             # Admin personalizado con widget de imágenes
│   ├── widgets.py           # Widget personalizado para selección de imágenes
│   ├── ai_generator.py      # Integración con Google Gemini AI
│   ├── image_services.py    # Servicios de generación de imágenes
│   ├── utils.py             # Utilidades para manejo seguro de archivos
│   └── managers.py          # Managers personalizados para optimización
├── 📁 templates/            # Templates HTML
│   ├── base.html            # Template base con Tailwind CSS
│   ├── partials/            # Componentes reutilizables
│   ├── posts/               # Templates de posts
│   ├── accounts/            # Templates de usuarios
│   └── admin/               # Templates personalizados del admin
├── 📁 static/               # Archivos estáticos
│   ├── css/                 # Estilos personalizados
│   ├── js/                  # JavaScript y Alpine.js
│   └── img/                 # Imágenes del sitio
├── 📁 media/                # Archivos subidos por usuarios
│   ├── post_images/         # Imágenes de posts
│   └── ai_posts/            # Imágenes extraídas por IA
├── 📁 staticfiles/          # Archivos estáticos recolectados
├── 📋 requirements.txt      # Dependencias Python
├── ⚙️ .env                  # Variables de entorno
├── 🗃️ db.sqlite3           # Base de datos SQLite (desarrollo)
└── 🐍 manage.py             # Script de gestión de Django
```

---

## 🤖 Generador de IA

### ✨ **Características Principales**

- **🧠 Google Gemini 2.5-pro**: Integración con el modelo de IA más avanzado de Google
- **🔗 Extracción de URLs**: Analiza y extrae contenido automáticamente desde cualquier URL
- **🖼️ Procesamiento de Imágenes**: Descarga y procesa imágenes encontradas en el contenido
- **📝 Reescritura Inteligente**: Convierte contenido en artículos únicos con formato HTML
- **🏷️ Generación de Tags**: Crea etiquetas relevantes automáticamente
- **🎯 Selección de Cabecera**: Widget inteligente para seleccionar imágenes de cabecera

### 🚀 **Cómo Usar el Generador**

1. **Accede al Admin**: Ve a `/admin/posts/post/`
2. **Generador de IA**: Haz clic en "Generar Post con IA"
3. **Ingresa URL**: Pega la URL del artículo que quieres procesar
4. **Configura Opciones**: 
   - Selecciona el tipo de prompt
   - Activa extracción de imágenes
   - Ajusta el número máximo de imágenes
5. **Genera**: El sistema creará automáticamente:
   - Título optimizado
   - Contenido reescrito en HTML
   - Tags relevantes
   - Imágenes extraídas y procesadas

### 🛠️ **Configuración Avanzada**

El sistema incluye templates de prompts personalizables para diferentes tipos de contenido:
- **Reescritura Simple**: Para contenido básico
- **Post Completo**: Para artículos detallados con estructura HTML
- **Generación de Tags**: Para crear etiquetas específicas

---

---

## � Funcionralidades Destacadas

### 🎨 **Widget Personalizado de Imágenes**
- Selector visual de imágenes existentes
- Preview en tiempo real
- Validación automática de archivos
- Soporte para múltiples formatos (JPG, PNG, WebP, etc.)

### 🔒 **Seguridad Avanzada**
- Validación segura de archivos
- Protección contra directory traversal
- Manejo robusto de errores
- Logging estructurado para debugging

### ⚡ **Optimización de Rendimiento**
- Managers personalizados para consultas optimizadas
- Caching inteligente de imágenes
- Lazy loading de contenido
- Compresión automática de archivos estáticos

---

## 👨‍💻 Autor

<div align="center">

**SkuuIll**

[![GitHub](https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white)](https://github.com/SkuuIll)


</div>

---

## 🎓 Proyecto Final - Informatorio Chaco 2025

Este proyecto fue desarrollado como **Proyecto Final** para el curso de **Desarrollo Web con Python y Django** del programa **Informatorio Chaco 2025**.

### 🏆 **Logros del Proyecto**
- ✅ Implementación completa de CRUD con Django
- ✅ Integración exitosa con APIs de IA (Google Gemini)
- ✅ Sistema de autenticación y autorización robusto
- ✅ UI/UX moderna y responsiva
- ✅ Optimización de rendimiento y seguridad
- ✅ Código limpio y bien documentado

### 🙏 **Agradecimientos**
- 🏫 **Informatorio Chaco** - Por la oportunidad de formación
- 👨‍🏫 **Instructores** - Por la guía y conocimientos compartidos
- 👥 **Compañeros** - Por el apoyo y colaboración
- 🌐 **Comunidad Open Source** - Por las herramientas increíbles

---

<div align="center">

### ⭐ ¡Si te gusta este proyecto, dale una estrella!

**Hecho con ❤️ en Chaco, Argentina 🇦🇷**

*Proyecto Final - Informatorio 2025*

</div>
