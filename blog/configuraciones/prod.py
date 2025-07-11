from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Actualiza esto con tu dominio real en producción
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# --- Configuración de Whitenoise para archivos estáticos ---

# Añadir Whitenoise al middleware. Debe estar después de SecurityMiddleware y antes que todos los demás.
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# Almacenamiento de archivos estáticos para producción
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- Configuraciones de Seguridad para Producción ---

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# --- Configuración de Email para Producción ---
# Reemplaza esto con tu configuración de email real (ej. SendGrid, Mailgun)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.example.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASS')
