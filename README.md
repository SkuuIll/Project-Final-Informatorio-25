# Proyecto Final: Blog con Django

Este repositorio contiene un proyecto de blog funcional construido con Python y Django. Fue desarrollado como proyecto final para el curso de Desarrollo Web de Informatorio Chaco.

---

## 🚀 Live Demo

[Link a la demo en vivo](https://proyecto.skulll.site/)

---

## ✨ Características Principales

*   **Autenticación de Usuarios:**
    *   Registro, inicio y cierre de sesión.
    *   Recuperación de contraseña.
    *   Perfiles de usuario personalizables con avatares.
*   **Dashboard Personalizado:**
    *   Panel de control para que los usuarios administren sus posts.
    *   Estadísticas de rendimiento de los posts (vistas, likes, comentarios).
    *   Gráfico de actividad de los posts.
*   **Gestión de Contenido:**
    *   Creación, edición y eliminación de posts.
    *   Editor de texto enriquecido (`django-ckeditor-5`).
    *   Sistema de etiquetas (`django-taggit`).
    *   Cálculo automático del tiempo de lectura.
*   **Interacción Social:**
    *   Sistema de comentarios anidados.
    *   Sistema de "Me Gusta" y "Favoritos".
    *   Notificaciones en tiempo real para nuevos comentarios y seguidores.
*   **Roles y Permisos:**
    *   **Administrador:** Control total sobre el sitio.
    *   **Usuario Registrado:** Puede crear posts (previa autorización), comentar y seguir a otros usuarios.
    *   **Visitante:** Solo puede leer los posts.
*   **API REST:**
    *   API para acceder a los posts (`djangorestframework`).
*   **Seguridad:**
    *   Protección contra CSRF y XSS.
    *   Verificación de usuarios con `django-turnstile`.
*   **Otras Características:**
    *   Búsqueda de posts por título o contenido.
    *   Feed RSS para los últimos posts.
    *   Panel de administración personalizado con `django-jazzmin`.

---

## 🛠️ Stack Tecnológico

*   **Backend:**
    *   Python 3
    *   Django
    *   Channels (para WebSockets)
*   **Frontend:**
    *   HTML5, CSS3
    *   Tailwind CSS
    *   Alpine.js
*   **Base de Datos:**
    *   SQLite 3 (para desarrollo)
    *   PostgreSQL (para producción, vía Docker)
*   **Dependencias Clave:**
    *   `djangorestframework`
    *   `django-jazzmin`
    *   `django-ckeditor-5`
    *   `django-turnstile`
    *   `django-taggit`
    *   `django-crispy-forms`
    *   `crispy-bootstrap5`
    *   `django-extensions`
    *   `python-dotenv`

---

## 🚀 Cómo Empezar

### Con Docker (Recomendado)

La forma más sencilla de poner en marcha este proyecto es usando Docker y Docker Compose.

1.  **Clonar el Repositorio:**

    ```bash
    git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
    cd Project-Final-Informatorio-25
    ```

2.  **Crear el archivo `.env`:**

    Crea un archivo `.env` en la raíz del proyecto y añade las siguientes variables:

    ```
    SECRET_KEY=tu_super_secreto_aqui
    DEBUG=True
    ```

3.  **Iniciar los Contenedores:**

    ```bash
    docker-compose up -d --build
    ```

¡Listo! Abre tu navegador y visita **`http://localhost:8000`**. Para gestionar el contenido, accede a **`http://localhost:8000/admin`**.

### Instalación Local

Si prefieres no usar Docker, puedes seguir estos pasos para una instalación local.

1.  **Clonar el Repositorio:**

    ```bash
    git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
    cd Project-Final-Informatorio-25
    ```

2.  **Crear y Activar el Entorno Virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3.  **Instalar Dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Crear el archivo `.env`:**

    Crea un archivo `.env` en la raíz del proyecto y añade las siguientes variables:

    ```
    SECRET_KEY=tu_super_secreto_aqui
    DEBUG=True
    ```

5.  **Aplicar Migraciones:**

    ```bash
    python manage.py migrate
    ```

6.  **Crear un Superusuario:**

    ```bash
    python manage.py createsuperuser
    ```

7.  **Ejecutar el Servidor:**

    ```bash
    python manage.py runserver
    ```

Ahora puedes acceder al sitio en **`http://localhost:8000`**.

---

## ⚙️ Comandos Útiles

*   **Crear un superusuario:**

    ```bash
    python manage.py createsuperuser
    ```

*   **Ejecutar migraciones:**

    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

*   **Correr pruebas:**

    ```bash
    python manage.py test
    ```

*   **Actualizar el tiempo de lectura de los posts:**

    ```bash
    python manage.py runscript update_reading_time
    ```

---

## 📁 Estructura del Proyecto

```
Project-Final/
├── accounts/             # App para gestión de usuarios y perfiles
├── blog/                 # App principal del proyecto, contiene la configuración
│   └── configuraciones/  # Módulos de settings
├── posts/                # App para la lógica de los posts, comentarios, etc.
│   └── scripts/          # Scripts personalizados para `runscript`
├── templates/            # Plantillas HTML globales
├── static/               # Archivos estáticos (CSS, JS, imágenes)
├── media/                # Archivos subidos por los usuarios
├── .env                  # Archivo de variables de entorno (NO versionado)
├── manage.py             # Script de gestión de Django
└── requirements.txt      # Dependencias de Python
```

---

## 👤 Autor

*   **SkuuIll** - *Desarrollo del proyecto* - [Perfil de GitHub](https://github.com/SkuuIll)

---

## 🎓 Agradecimientos

Este proyecto fue desarrollado como parte del trayecto formativo de **Informatorio Chaco**.
