# Proyecto Final: Blog con Django

Este repositorio contiene un proyecto de blog funcional construido con Python y Django. Fue desarrollado como proyecto final para el curso de Desarrollo Web de Informatorio Chaco.

---

## 🚀 Live Demo

[Link a la demo en vivo](https://tu-demo-en-vivo.com)

---

## ✨ Características

*   **Autenticación de Usuarios:** Registro, inicio y cierre de sesión.
*   **Dashboard Personalizado:** Un panel de control para que los usuarios administren sus posts, vean estadísticas y más.
*   **Gestión de Contenido:** Creación, edición y eliminación de posts a través de un panel de administración (`django-jazzmin`).
*   **Roles y Permisos:**
    *   **Administrador:** Control total.
    *   **Usuario Registrado:** Puede comentar en las publicaciones.
    *   **Visitante:** Solo puede leer.
*   **Comentarios:** Sistema de comentarios para usuarios autenticados.
*   **Búsqueda:** Funcionalidad de búsqueda para encontrar posts por título o contenido.
*   **Editor de Texto Enriquecido:** `django-ckeditor-5` para una mejor experiencia al escribir posts.
*   **Seguridad:** Protección contra CSRF y XSS, y uso de `django-turnstile` para verificar a los usuarios.

---

## 🛠️ Tecnologías Utilizadas

*   **Backend:** Python, Django
*   **Base de Datos:** SQLite 3 (para desarrollo)
*   **Frontend:** HTML5, CSS3, Bootstrap 5 (`crispy-bootstrap5`)
*   **Dependencias Clave:**
    *   `djangorestframework`
    *   `django-jazzmin` (para un admin theme moderno)
    *   `django-ckeditor-5`
    *   `django-turnstile`
    *   `django-taggit` (para el sistema de etiquetas)
    *   `django-guardian` (para permisos a nivel de objeto)
    *   `python-dotenv` (para gestionar variables de entorno)

---

## 🐳 Ejecutar con Docker

La forma más sencilla de poner en marcha este proyecto es usando Docker y Docker Compose.

### 1. Clonar el Repositorio

```bash
git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
cd Project-Final-Informatorio-25
```

### 2. Iniciar los Contenedores

```bash
docker-compose up -d --build
```

¡Listo! Abre tu navegador y visita **`http://localhost:8000`**. Para gestionar el contenido, accede a **`http://localhost:8000/admin`**.

Para detener los contenedores, ejecuta:

```bash
docker-compose down
```

---

## 📁 Estructura del Proyecto

```
Project-Final/
├── accounts/             # App para gestión de usuarios y perfiles
├── blog/                 # App principal del proyecto, contiene la configuración
│   └── configuraciones/  # Módulos de settings (base, local, prod)
├── posts/                # App para la lógica de los posts, comentarios, etc.
├── templates/            # Plantillas HTML globales
├── static/               # Archivos estáticos (CSS, JS, imágenes)
├── media/                # Archivos subidos por los usuarios
├── .env                  # Archivo de variables de entorno (NO versionado)
├── manage.py             # Script de gestión de Django
└── requirements.txt      # Dependencias de Python
```



## 👤 Autor

*   **SkuuIll** - *Desarrollo del proyecto* - [Perfil de GitHub](https://github.com/SkuuIll)

---

## 🎓 Agradecimientos 

Este proyecto fue desarrollado como parte del trayecto formativo de **Informatorio Chaco**.
