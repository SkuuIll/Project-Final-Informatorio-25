from .base import *
import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Configuración de email para desarrollo (imprime en consola)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
