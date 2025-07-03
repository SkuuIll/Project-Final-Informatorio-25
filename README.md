# Proyecto Final: Blog con Django (Informatorio Chaco)

Este repositorio contiene el proyecto final desarrollado para el curso de Desarrollo Web de Informatorio Chaco. Se trata de una aplicación web de blog completamente funcional, construida desde cero utilizando Python y el framework Django.

![Imagen de la página de inicio del blog](https://raw.githubusercontent.com/SkuuIll/Project-Final-Informatorio-25/refs/heads/main/screen/Grabaci%C3%B3n.gif)

---

## 🚀 Descripción del Proyecto

El objetivo de este proyecto es aplicar los conocimientos adquiridos durante el curso para construir una aplicación web robusta y escalable. El blog permite a los administradores gestionar el contenido y a los usuarios registrarse para interactuar con las publicaciones a través de comentarios.

---

## ✨ Características Principales

* **Sistema de Autenticación Completo:** Funcionalidades de registro de nuevos usuarios, inicio de sesión (login) y cierre de sesión (logout).
* **Gestión de Contenido:** Los administradores pueden crear, editar y eliminar posts desde el panel de administración de Django.
* **Roles de Usuario:**
    * **Administrador:** Control total sobre usuarios y publicaciones.
    * **Usuario Registrado:** Puede ver todos los posts y añadir comentarios.
    * **Visitante:** Puede leer los posts pero no puede comentar.
* **Sistema de Comentarios:** Los usuarios autenticados pueden dejar comentarios en las publicaciones.
* **Organización del Contenido:** Los posts están organizados por categorías, facilitando la navegación.
* **Diseño Responsivo:** La interfaz se adapta correctamente a dispositivos móviles, tabletas y ordenadores de escritorio.

---

## 🛠️ Tecnologías Utilizadas

* **Backend:** Python, Django
* **Base de Datos:** SQLite 3 (para desarrollo)
* **Frontend:** HTML5, CSS3, Tailwind CSS
* **Gestión de Dependencias:** Pip, `requirements.txt`
* **Control de Versiones:** Git, GitHub

---

## ⚙️ Guía de Instalación y Puesta en Marcha

Para ejecutar este proyecto en tu máquina local, sigue estos pasos:

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/SkuuIll/Project-Final-Informatorio-25.git](https://github.com/SkuuIll/Project-Final-Informatorio-25.git)
    ```

2.  **Navegar a la carpeta del proyecto:**
    ```bash
    cd Project-Final-Informatorio-25
    ```

3.  **Crear y activar un entorno virtual:**
    ```bash
    # Crear el entorno
    python -m venv entorno

    # Activar en Windows
    .\entorno\Scripts\activate

    # Activar en macOS/Linux
    source entorno/bin/activate
    ```

4.  **Instalar las dependencias del proyecto:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Aplicar las migraciones a la base de datos:**
    ```bash
    python manage.py migrate
    ```

6.  **Crear un superusuario** para acceder al panel de administración:
    ```bash
    python manage.py createsuperuser
    ```
    (Sigue las instrucciones para crear tu usuario y contraseña de administrador).

7.  **Iniciar el servidor de desarrollo:**
    ```bash
    python manage.py runserver
    ```

8.  **¡Listo!** Abre tu navegador y visita `http://127.0.0.1:8000` para ver la aplicación en funcionamiento. Para gestionar el contenido, accede a `http://127.0.0.1:8000/admin`.

---

## 📁 Estructura del Proyecto

El proyecto sigue la estructura recomendada en el curso, separando la lógica en diferentes aplicaciones y manteniendo una configuración ordenada:



    mi_proyecto/
    ├── apps/                 # Directorio para tus aplicaciones de Django
    ├── media/                # Para archivos subidos por los usuarios
    ├── static/               # Directorio para las aplicaciones de Django (posts, usuarios, etc.)
    ├── media/                # Archivos subidos por los usuarios (ej: imágenes de posts)
    ├── static/               # Archivos estáticos (CSS, JS, imágenes de la plantilla)
    ├── templates/            # Plantillas HTML globales
    └── mi_proyecto/
    ├── configuraciones/      # Carpeta para los archivos de settings
    └── ...


---

## 👤 Autor

* **SkuuIll** - *Desarrollo del proyecto* - [Perfil de GitHub](https://github.com/SkuuIll)

---

## 🎓 Agradecimientos

Este proyecto fue desarrollado como parte del trayecto formativo de **Informatorio Chaco**, un programa de capacitación en tecnología que impulsa el desarrollo de habilidades digitales en la región.
