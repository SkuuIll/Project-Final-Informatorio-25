#!/bin/bash

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando DevBlog...${NC}"

# Función para esperar que la base de datos esté lista
wait_for_db() {
    echo -e "${YELLOW}⏳ Esperando que PostgreSQL esté listo...${NC}"
    
    while ! pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER; do
        echo -e "${YELLOW}⏳ PostgreSQL no está listo - esperando...${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}✅ PostgreSQL está listo!${NC}"
}

# Función para esperar que Redis esté listo
wait_for_redis() {
    echo -e "${YELLOW}⏳ Esperando que Redis esté listo...${NC}"
    
    while ! redis-cli -h redis ping > /dev/null 2>&1; do
        echo -e "${YELLOW}⏳ Redis no está listo - esperando...${NC}"
        sleep 2
    done
    
    echo -e "${GREEN}✅ Redis está listo!${NC}"
}

# Esperar servicios si están configurados
if [ "$USE_POSTGRESQL" = "True" ]; then
    wait_for_db
fi

if [ -n "$REDIS_URL" ]; then
    wait_for_redis
fi

# Ejecutar migraciones
echo -e "${YELLOW}📊 Ejecutando migraciones de base de datos...${NC}"
python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Migraciones completadas exitosamente${NC}"
else
    echo -e "${RED}❌ Error en las migraciones${NC}"
    exit 1
fi

# Recopilar archivos estáticos
echo -e "${YELLOW}📦 Recopilando archivos estáticos...${NC}"
python manage.py collectstatic --noinput

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Archivos estáticos recopilados${NC}"
else
    echo -e "${RED}❌ Error recopilando archivos estáticos${NC}"
    exit 1
fi

# Crear superusuario si no existe (solo en desarrollo)
if [ "$DEBUG" = "True" ]; then
    echo -e "${YELLOW}👤 Verificando superusuario...${NC}"
    python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('✅ Superusuario creado: admin/admin123')
else:
    print('✅ Superusuario ya existe')
"
fi

echo -e "${GREEN}🎉 DevBlog iniciado correctamente!${NC}"

# Ejecutar el comando pasado como argumentos
exec "$@"