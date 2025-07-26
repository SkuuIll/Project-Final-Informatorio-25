#!/bin/bash

echo "🖼️  Arreglando archivos media..."

# Detener contenedores
echo "⏹️  Deteniendo contenedores..."
docker-compose down

# Crear directorios en el host para que Nginx pueda acceder
echo "📁 Creando directorios..."
mkdir -p /home/project/project/media
mkdir -p /home/project/project/staticfiles

# Iniciar contenedores con bind mounts
echo "🚀 Iniciando contenedores..."
docker-compose up -d

# Esperar y configurar permisos para Nginx del servidor
echo "⏳ Configurando permisos para Nginx..."
sleep 15
chown -R www-data:www-data /home/project/project/media/
chown -R www-data:www-data /home/project/project/staticfiles/
chmod -R 755 /home/project/project/media/
chmod -R 755 /home/project/project/staticfiles/

# Recargar Nginx del servidor
echo "🔄 Recargando Nginx..."
systemctl reload nginx

echo "✅ Completado. Las imágenes ahora deberían funcionar."
echo "🧪 Prueba subiendo una imagen y visitando: https://proyecto.skulll.site/media/[archivo]"