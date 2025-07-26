#!/bin/bash

echo "🚀 Iniciando servidor Django optimizado..."

# Crear directorios necesarios
mkdir -p /app/logs /app/media /app/staticfiles

# Ejecutar migraciones
echo "📊 Ejecutando migraciones..."
python manage.py migrate

# Recopilar archivos estáticos
echo "📁 Recopilando archivos estáticos..."
python manage.py collectstatic --noinput

# Inicializar sistema de tags
echo "🏷️  Inicializando sistema de tags..."
python manage.py initialize_tag_system --calculate-cooccurrence --create-history

# Monitoreo de memoria (opcional)
if python -c "import psutil" 2>/dev/null; then
    echo "💾 Iniciando monitoreo de memoria..."
    python monitor_memory.py --threshold 85 --interval 60 &
    MONITOR_PID=$!
    trap "kill $MONITOR_PID 2>/dev/null; exit 0" SIGTERM SIGINT
fi

# Iniciar servidor Gunicorn
echo "🌐 Iniciando servidor Gunicorn..."
exec gunicorn --config gunicorn_config.py blog.wsgi:application