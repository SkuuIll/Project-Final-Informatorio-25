#!/bin/bash

echo "🤖 Arreglando timeouts para generación de IA..."

# Buscar archivo de configuración de Nginx
NGINX_CONFIG=""
for config in "/etc/nginx/sites-available/proyecto.skulll.site" "/etc/nginx/sites-available/default"; do
    if [ -f "$config" ]; then
        NGINX_CONFIG="$config"
        break
    fi
done

if [ -z "$NGINX_CONFIG" ]; then
    echo "❌ No se encontró configuración de Nginx"
    exit 1
fi

echo "📝 Configurando timeouts en: $NGINX_CONFIG"

# Crear backup
cp "$NGINX_CONFIG" "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"

# Actualizar timeouts para IA (5 minutos)
sed -i '/proxy_connect_timeout/c\        proxy_connect_timeout 300s;' "$NGINX_CONFIG"
sed -i '/proxy_send_timeout/c\        proxy_send_timeout 300s;' "$NGINX_CONFIG"
sed -i '/proxy_read_timeout/c\        proxy_read_timeout 300s;' "$NGINX_CONFIG"

# Añadir timeout adicional si no existe
if ! grep -q "proxy_next_upstream_timeout" "$NGINX_CONFIG"; then
    sed -i '/proxy_read_timeout/a\        proxy_next_upstream_timeout 300s;' "$NGINX_CONFIG"
fi

# Verificar sintaxis y recargar
if nginx -t; then
    echo "🔄 Recargando Nginx..."
    systemctl reload nginx
    echo "✅ Timeouts configurados para 5 minutos"
else
    echo "❌ Error en sintaxis, restaurando backup..."
    cp "${NGINX_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)" "$NGINX_CONFIG"
    exit 1
fi

echo "✅ Configuración completada. La generación de IA ahora tiene 5 minutos de timeout."