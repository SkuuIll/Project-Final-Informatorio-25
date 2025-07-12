#!/bin/sh

# Esperar a que la base de datos esté lista
while ! nc -z db 5432; do
  echo "Esperando a la base de datos..."
  sleep 1
done

# Ejecutar las migraciones de la base de datos
python manage.py migrate

# Iniciar el servidor
python manage.py runserver 0.0.0.0:8000
