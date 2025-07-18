#!/bin/bash

# --- Script de Configuración de Servidor para Proyecto Django con Docker ---

# Colores para la salida
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para imprimir mensajes informativos
info() {
    echo -e "${GREEN}[INFO] $1${NC}"
}

# Función para imprimir advertencias
warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# Verificar si el script se ejecuta como root
if [ "$(id -u)" -ne 0 ]; then
  warn "Este script debe ser ejecutado como root o con privilegios sudo."
  exit 1
fi

# --- 1. Recopilar información del usuario ---
info "Iniciando la configuración del servidor..."

read -p "Introduce tu nombre de dominio (ej. mi-proyecto.com): " DOMAIN
read -p "Introduce tu email (para notificaciones de SSL): " EMAIL
GIT_REPO="https://github.com/SkuuIll/Project-Final-Informatorio-25"
read -p "Introduce el nombre para un nuevo usuario sudo (no-root): " NEW_USER
info "Ahora, configuremos el superusuario para Django."
read -p "Nombre de usuario para el admin de Django: " DJANGO_SUPERUSER
read -s -p "Contraseña para el admin de Django (no se mostrará): " DJANGO_PASSWORD
echo
read -p "Email para el admin de Django: " DJANGO_EMAIL

# Obtener la IP pública del servidor para agregarla a ALLOWED_HOSTS
SERVER_IP=$(curl -s ifconfig.me || hostname -I | awk '{print $1}')

# --- 2. Crear un nuevo usuario sudo ---
info "Creando un nuevo usuario '$NEW_USER' con privilegios sudo..."
adduser $NEW_USER
usermod -aG sudo $NEW_USER
info "Usuario '$NEW_USER' creado. Por favor, inicia sesión como este usuario para futuras operaciones."

# --- 3. Instalar dependencias del sistema ---
info "Actualizando el sistema e instalando dependencias (Docker, Docker Compose, Nginx, Certbot)..."
apt-get update && apt-get upgrade -y
apt-get install -y apt-transport-https ca-certificates curl software-properties-common

info "Agregando el repositorio Universe..."
add-apt-repository universe
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx

# Instalar Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Instalar Docker Compose
COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d \" -f 4)
curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Añadir el nuevo usuario al grupo de docker
usermod -aG docker $NEW_USER

info "Dependencias instaladas correctamente."

# --- 4. Clonar el proyecto y configurar el entorno ---
info "Cambiando al directorio del nuevo usuario para clonar el proyecto..."
su - $NEW_USER -c "
    set -e; 
    cd /home/$NEW_USER; 
    echo '[INFO] Clonando el repositorio desde $GIT_REPO...'; 
    git clone $GIT_REPO project; 
    cd project; 
    echo '[INFO] Creando el archivo .env...'; 
    touch .env; 
    echo 'POSTGRES_DB=postgres' >> .env; 
    echo 'POSTGRES_USER=postgres' >> .env; 
    echo 'POSTGRES_PASSWORD=postgres' >> .env; 
    echo 'SECRET_KEY=\$(openssl rand -hex 32)' >> .env; 
    echo 'DEBUG=0' >> .env; 
    echo "ALLOWED_HOSTS=$DOMAIN,localhost,$SERVER_IP" >> .env;
    echo '[INFO] .env creado con valores por defecto. ¡Recuerda cambiarlos si es necesario!'; 
"

# --- 5. Ajustar Permisos para Nginx ---
info "Ajustando permisos de directorio para que Nginx pueda acceder a los archivos..."
# Agrega el usuario de nginx (www-data) al grupo de tu nuevo usuario
usermod -aG $NEW_USER www-data
chmod 710 /home/$NEW_USER

# --- 5. Configurar Nginx como proxy inverso ---
info "Configurando Nginx para el dominio $DOMAIN..."

cat > /etc/nginx/sites-available/$DOMAIN << EOL
server { 
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    location /static/ {
        alias /home/$NEW_USER/project/staticfiles/;
    }

    location /media/ {
        alias /home/$NEW_USER/project/media/;
    }
}
EOL

# Usamos -sf para forzar la creación del enlace simbólico, sobreescribiéndolo si ya existe
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Probar la configuración de Nginx
nginx -t
if [ $? -ne 0 ]; then
  warn "La configuración de Nginx tiene errores. Revisa el archivo /etc/nginx/sites-available/$DOMAIN."
  exit 1
fi

# --- 6. Obtener certificado SSL con Certbot ---
info "Obteniendo certificado SSL para $DOMAIN..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect
if [ $? -ne 0 ]; then
  warn "Certbot falló al obtener el certificado SSL. Revisa la configuración de Nginx y los registros de Certbot."
  exit 1
fi

info "Certificado SSL obtenido e instalado."

# --- 7. Iniciar la aplicación con Docker Compose ---
info "Iniciando la aplicación con Docker Compose..."

su - $NEW_USER -c "
    cd /home/$NEW_USER/project && 
    docker-compose up -d --build
"

# --- 8. Crear y ajustar permisos para el directorio de media ---
info "Ajustando permisos para el directorio /media/ para que Nginx pueda servir los archivos subidos..."
# Crear el directorio como el nuevo usuario
su - $NEW_USER -c "mkdir -p /home/$NEW_USER/project/media"
# Cambiar el propietario para que el grupo www-data (de Nginx) pueda leer/escribir
chown -R $NEW_USER:www-data /home/$NEW_USER/project/media
# Dar permisos de lectura/escritura al grupo y añadir el bit 'setgid'
# El setgid bit ('g+s') asegura que los nuevos archivos creados dentro de /media 
# hereden el grupo 'www-data', solucionando problemas de permisos para futuras subidas.
chmod -R 775 /home/$NEW_USER/project/media
chmod g+s /home/$NEW_USER/project/media

# --- 8. Crear Superusuario de Django ---
info "Creando un superusuario de Django ($DJANGO_SUPERUSER)..."
info "Esperando a que la base de datos se inicie (15 segundos)..."
sleep 15

docker-compose -f /home/$NEW_USER/project/docker-compose.yml exec -T web python manage.py shell <<EOF
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='$DJANGO_SUPERUSER').exists():
    User.objects.create_superuser('$DJANGO_SUPERUSER', '$DJANGO_EMAIL', '$DJANGO_PASSWORD')
    print('Superusuario "$DJANGO_SUPERUSER" creado con éxito.')
else:
    print('El superusuario "$DJANGO_SUPERUSER" ya existe.')
EOF

info "¡Despliegue completado!"
info "Tu sitio está disponible en https://$DOMAIN"
info "A partir de ahora, gestiona tu aplicación desde el directorio /home/$NEW_USER/project como el usuario '$NEW_USER'."
info "Puedes acceder al panel de admin con el usuario '$DJANGO_SUPERUSER'."
