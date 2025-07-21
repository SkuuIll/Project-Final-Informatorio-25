# Guía de Instalación - DevBlog

## Requisitos del Sistema

- Python 3.8 o superior
- PostgreSQL 12 o superior (opcional, SQLite por defecto)
- Node.js 16 o superior (para desarrollo frontend)
- Git

## Instalación Local

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd devblog
```

### 2. Crear Entorno Virtual

```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
# Django
SECRET_KEY=tu-clave-secreta-muy-segura
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Base de datos (opcional - PostgreSQL)
USE_POSTGRESQL=False
POSTGRES_DB=devblog
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Cloudflare Turnstile (opcional)
TURNSTILE_SITE_KEY=tu-site-key
TURNSTILE_SECRET_KEY=tu-secret-key

# Google AI (opcional)
GOOGLE_API_KEY=tu-api-key
```

### 5. Configurar Base de Datos

#### Opción A: SQLite (por defecto)
```bash
python manage.py migrate
```

#### Opción B: PostgreSQL
1. Instalar PostgreSQL
2. Crear base de datos:
```sql
CREATE DATABASE devblog;
CREATE USER devblog_user WITH PASSWORD 'tu-password';
GRANT ALL PRIVILEGES ON DATABASE devblog TO devblog_user;
```
3. Configurar `.env` con `USE_POSTGRESQL=True`
4. Ejecutar migraciones:
```bash
python manage.py migrate
```

### 6. Crear Superusuario

```bash
python manage.py createsuperuser
```

### 7. Cargar Datos de Prueba (opcional)

```bash
python manage.py loaddata fixtures/sample_data.json
```

### 8. Ejecutar Servidor de Desarrollo

```bash
python manage.py runserver
```

El sitio estará disponible en `http://127.0.0.1:8000/`

## Instalación con Docker

### 1. Usando Docker Compose

```bash
# Construir y ejecutar
docker-compose up --build

# En segundo plano
docker-compose up -d --build
```

### 2. Ejecutar Migraciones

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

## Configuración de Producción

### 1. Variables de Entorno de Producción

```env
DEBUG=False
SECRET_KEY=clave-super-secreta-para-produccion
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
USE_POSTGRESQL=True
```

### 2. Configurar Servidor Web

#### Nginx + Gunicorn

1. Instalar Gunicorn:
```bash
pip install gunicorn
```

2. Crear archivo de configuración Gunicorn:
```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

3. Configurar Nginx:
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location /static/ {
        alias /path/to/devblog/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/devblog/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 3. SSL/HTTPS

```bash
# Usando Certbot
sudo certbot --nginx -d tu-dominio.com
```

## Solución de Problemas

### Error: "No module named 'psycopg2'"
```bash
# En Ubuntu/Debian
sudo apt-get install python3-dev libpq-dev
pip install psycopg2-binary

# En CentOS/RHEL
sudo yum install python3-devel postgresql-devel
pip install psycopg2-binary
```

### Error: "Permission denied" en archivos estáticos
```bash
python manage.py collectstatic
sudo chown -R www-data:www-data /path/to/staticfiles/
```

### Error de migraciones
```bash
# Resetear migraciones (¡CUIDADO: borra datos!)
python manage.py migrate --fake-initial
```

## Comandos Útiles

```bash
# Ejecutar tests
python manage.py test

# Crear migración
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic

# Crear superusuario
python manage.py createsuperuser

# Shell de Django
python manage.py shell

# Verificar configuración
python manage.py check
```