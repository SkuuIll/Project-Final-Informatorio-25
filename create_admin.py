#!/usr/bin/env python
import os
import django
from django.contrib.auth import get_user_model

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

User = get_user_model()

# Datos del superusuario
username = 'admin'
email = 'admin@proyecto.skulll.site'
password = 'admin123'  # Cambia esta contraseña

# Crear superusuario si no existe
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superusuario "{username}" creado exitosamente!')
else:
    print(f'El usuario "{username}" ya existe.')