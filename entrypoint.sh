#!/bin/sh

# Esperar a que la base de datos esté lista
while ! nc -z db 5432; do
  echo "Esperando a la base de datos..."
  sleep 1
done

# Ejecutar las migraciones de la base de datos
python manage.py migrate

# Recopilar archivos estáticos
python manage.py collectstatic --noinput

# Iniciar el servidor de producción con Gunicorn
exec gunicorn blog.wsgi:application --bind 0.0.0.0:8000 --workers 3