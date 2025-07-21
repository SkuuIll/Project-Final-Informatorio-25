# Guía de Configuración - DevBlog

## Variables de Entorno

### Core Django Settings

| Variable | Descripción | Valor por Defecto | Requerido |
|----------|-------------|-------------------|-----------|
| `SECRET_KEY` | Clave secreta de Django | - | ✅ |
| `DEBUG` | Modo debug | `False` | ❌ |
| `ALLOWED_HOSTS` | Hosts permitidos | `localhost,127.0.0.1` | ❌ |

### Base de Datos

| Variable | Descripción | Valor por Defecto | Requerido |
|----------|-------------|-------------------|-----------|
| `USE_POSTGRESQL` | Usar PostgreSQL | `False` | ❌ |
| `POSTGRES_DB` | Nombre de la BD | `devblog` | ❌ |
| `POSTGRES_USER` | Usuario de BD | `postgres` | ❌ |
| `POSTGRES_PASSWORD` | Contraseña de BD | - | ⚠️ |
| `POSTGRES_HOST` | Host de BD | `localhost` | ❌ |
| `POSTGRES_PORT` | Puerto de BD | `5432` | ❌ |

### Servicios Externos

| Variable | Descripción | Requerido |
|----------|-------------|-----------|
| `GOOGLE_API_KEY` | API Key de Google Gemini | ❌ |
| `TURNSTILE_SITE_KEY` | Cloudflare Turnstile Site Key | ❌ |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile Secret Key | ❌ |

### Email (Producción)

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `EMAIL_HOST` | Servidor SMTP | `smtp.gmail.com` |
| `EMAIL_PORT` | Puerto SMTP | `587` |
| `EMAIL_HOST_USER` | Usuario email | `tu-email@gmail.com` |
| `EMAIL_HOST_PASSWORD` | Contraseña/App Password | `tu-app-password` |
| `EMAIL_USE_TLS` | Usar TLS | `True` |

## Configuración por Entorno

### Desarrollo Local

```env
SECRET_KEY=django-insecure-dev-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
USE_POSTGRESQL=False
```

### Staging

```env
SECRET_KEY=secure-staging-key
DEBUG=False
ALLOWED_HOSTS=staging.tu-dominio.com
USE_POSTGRESQL=True
POSTGRES_DB=devblog_staging
```

### Producción

```env
SECRET_KEY=super-secure-production-key
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
USE_POSTGRESQL=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
```

## Configuración de Servicios

### Google Gemini AI

1. Ve a [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crea una nueva API Key
3. Agrega la key a tu `.env`:
```env
GOOGLE_API_KEY=tu-api-key-aqui
```

### Cloudflare Turnstile

1. Ve a [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Crea un nuevo sitio Turnstile
3. Obtén las keys y agrégalas:
```env
TURNSTILE_SITE_KEY=tu-site-key
TURNSTILE_SECRET_KEY=tu-secret-key
```

### PostgreSQL

#### Instalación Local

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres createdb devblog
sudo -u postgres createuser devblog_user
sudo -u postgres psql -c "ALTER USER devblog_user WITH PASSWORD 'password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE devblog TO devblog_user;"
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
createdb devblog
createuser devblog_user
psql -c "ALTER USER devblog_user WITH PASSWORD 'password';"
```

#### Docker
```yaml
# docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: devblog
      POSTGRES_USER: devblog_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

## Configuración de Logging

El sistema de logging está configurado automáticamente y crea archivos en el directorio `logs/`:

- `logs/devblog.log` - Log general de la aplicación
- `logs/errors.log` - Solo errores
- `logs/django.log` - Logs específicos de Django

### Personalizar Logging

Puedes modificar la configuración en `blog/configuraciones/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'custom_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/custom.log',
            'maxBytes': 1024*1024*10,  # 10 MB
            'backupCount': 3,
        },
    },
    'loggers': {
        'custom_logger': {
            'handlers': ['custom_file'],
            'level': 'INFO',
        },
    },
}
```

## Configuración de Cache

### Redis (Recomendado para Producción)

```env
# .env
REDIS_URL=redis://localhost:6379/1
```

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Memcached

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': '127.0.0.1:11211',
    }
}
```

## Configuración de Archivos Estáticos

### Desarrollo
Los archivos estáticos se sirven automáticamente desde `static/`.

### Producción
```python
# Configuración automática con Whitenoise
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### CDN (Opcional)
```python
# Para usar AWS S3 o similar
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'
AWS_STORAGE_BUCKET_NAME = 'tu-bucket'
AWS_S3_REGION_NAME = 'us-east-1'
```

## Configuración de Seguridad

### Headers de Seguridad
Configurados automáticamente en producción:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security` (HSTS)
- `Content-Security-Policy`

### HTTPS
```env
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## Monitoreo y Métricas

### Sentry (Recomendado)
```env
SENTRY_DSN=https://tu-dsn@sentry.io/proyecto
```

```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### Health Checks
El proyecto incluye endpoints de health check:
- `/health/` - Estado general
- `/health/db/` - Estado de la base de datos
- `/health/cache/` - Estado del cache

## Troubleshooting

### Problemas Comunes

**Error: "SECRET_KEY not found"**
```bash
# Asegúrate de tener el archivo .env
cp .env.example .env
# Edita .env con tus configuraciones
```

**Error de conexión a PostgreSQL**
```bash
# Verifica que PostgreSQL esté corriendo
sudo systemctl status postgresql
# Verifica la configuración en .env
```

**Archivos estáticos no se cargan**
```bash
python manage.py collectstatic
```

**Error de permisos**
```bash
# En Linux/Mac
chmod +x manage.py
# Verifica permisos de directorios
sudo chown -R $USER:$USER .
```