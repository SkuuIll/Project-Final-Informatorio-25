#!/bin/bash

echo "🚀 Iniciando servidor Django optimizado..."

# Crear directorios necesarios
mkdir -p /app/logs
mkdir -p /app/media
mkdir -p /app/staticfiles

# Configurar permisos
chmod 755 /app/logs
chmod 755 /app/media
chmod 755 /app/staticfiles

# Ejecutar migraciones
echo "📊 Ejecutando migraciones..."
python manage.py migrate

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Inicializar sistema de tags
echo "🏷️  Inicializando sistema de tags..."
python manage.py initialize_tag_system --calculate-cooccurrence --create-history

# Mostrar estado inicial de memoria
echo "💾 Estado inicial de memoria:"
python monitor_memory.py --once

# Iniciar monitoreo de memoria en background
echo "📈 Iniciando monitoreo de memoria..."
python monitor_memory.py --threshold 85 --interval 60 &
MONITOR_PID=$!

# Función para limpiar al salir
cleanup() {
    echo "🛑 Deteniendo servidor..."
    kill $MONITOR_PID 2>/dev/null
    exit 0
}

# Configurar trap para limpieza
trap cleanup SIGTERM SIGINT

# Iniciar servidor Gunicorn con configuración optimizada
echo "🌐 Iniciando servidor Gunicorn..."
exec gunicorn --config gunicorn_config.py blog.wsgi:application