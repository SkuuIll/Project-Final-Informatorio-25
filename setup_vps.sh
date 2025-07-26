#!/bin/bash

echo "🐧 Configuración para Ubuntu VPS"

# Verificar si estamos en el directorio correcto
if [ ! -f "manage.py" ]; then
    echo "❌ No se encontró manage.py. ¿Estás en el directorio del proyecto?"
    echo "📁 Directorio actual: $(pwd)"
    echo "📋 Archivos: $(ls -la)"
    exit 1
fi

echo "✅ Directorio del proyecto encontrado"

# Buscar entorno virtual
VENV_PATHS=(
    "venv"
    "env" 
    ".venv"
    "../venv"
    "/opt/venv"
    "/app/venv"
)

VENV_FOUND=""
for path in "${VENV_PATHS[@]}"; do
    if [ -d "$path" ] && [ -f "$path/bin/activate" ]; then
        echo "✅ Entorno virtual encontrado: $path"
        VENV_FOUND="$path"
        break
    fi
done

if [ -z "$VENV_FOUND" ]; then
    echo "❌ No se encontró entorno virtual"
    echo "💡 Creando entorno virtual..."
    python3 -m venv venv
    VENV_FOUND="venv"
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source "$VENV_FOUND/bin/activate"

# Verificar Django
echo "🔍 Verificando Django..."
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Django no está instalado"
    echo "💡 Instalando dependencias..."
    pip install -r requirements.txt 2>/dev/null || pip install django
fi

# Ejecutar script de configuración simple
echo "🔧 Ejecutando configuración simple..."
python3 find_media_path.py

# Intentar ejecutar configuración completa con Django
echo "🔧 Intentando configuración completa..."
if python -c "import django" 2>/dev/null; then
    echo "✅ Django disponible, ejecutando configuración completa..."
    python setup_ubuntu_permissions.py
else
    echo "⚠️ Django no disponible, solo configuración básica completada"
fi

# Buscar directorio media real
MEDIA_PATHS=(
    "./media"
    "/app/media"
    "/app/staticfiles"
    "./staticfiles"
)

echo "🔍 Buscando directorio media real..."
for path in "${MEDIA_PATHS[@]}"; do
    if [ -d "$path" ]; then
        echo "✅ Directorio media encontrado: $path"
        echo "🔧 Configurando permisos..."
        
        # Crear subdirectorios si no existen
        mkdir -p "$path/ai_posts/content"
        mkdir -p "$path/ai_posts/covers" 
        mkdir -p "$path/ai_posts/images"
        mkdir -p "$path/post_images"
        mkdir -p "$path/uploads"
        mkdir -p "$path/images"
        
        # Configurar permisos
        chmod -R 755 "$path" 2>/dev/null || echo "⚠️ No se pudieron cambiar permisos (requiere sudo)"
        
        echo "📝 Para configurar propietario, ejecuta:"
        echo "sudo chown -R www-data:www-data $path"
        echo "sudo chmod -R 755 $path"
        echo "sudo find $path -type f -exec chmod 644 {} \\;"
        
        break
    fi
done

echo "🎉 Configuración completada!"
echo "📝 Próximos pasos:"
echo "1. Ejecutar comandos sudo mostrados arriba"
echo "2. Reiniciar servidor web"
echo "3. Probar eliminación desde la galería"