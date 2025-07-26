#!/bin/bash

echo "=== DIAGNÓSTICO DE CONTENEDORES ==="
echo "Estado de contenedores:"
docker-compose ps

echo -e "\n=== LOGS DEL CONTENEDOR WEB ==="
docker-compose logs --tail=20 web

echo -e "\n=== LOGS DEL CONTENEDOR NGINX ==="
docker-compose logs --tail=20 nginx

echo -e "\n=== VERIFICAR CONECTIVIDAD INTERNA ==="
echo "Probando conexión desde nginx a web:"
docker-compose exec nginx wget -qO- http://web:8000 || echo "Error: No se puede conectar a web:8000"

echo -e "\n=== VERIFICAR PUERTOS ==="
echo "Puertos abiertos en el host:"
sudo netstat -tlnp | grep -E ':(80|8000|443)'

echo -e "\n=== PROBAR DJANGO DIRECTAMENTE ==="
echo "Probando Django en puerto 8000:"
curl -I http://localhost:8000 2>/dev/null || echo "Error: Django no responde en puerto 8000"

echo -e "\n=== PROBAR CON CLOUDFLARE HEADERS ==="
echo "Probando con headers de Cloudflare:"
curl -H "Host: proyecto.skulll.site" -H "X-Forwarded-Proto: https" -I http://localhost:8000 2>/dev/null || echo "Error con headers de Cloudflare"