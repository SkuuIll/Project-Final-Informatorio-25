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

# --- 2. Crear un nuevo usuario sudo ---
info "Creando un nuevo usuario '$NEW_USER' con privilegios sudo..."
adduser $NEW_USER
usermod -aG sudo $NEW_USER
info "Usuario '$NEW_USER' creado. Por favor, inicia sesión como este usuario para futuras operaciones."

# --- 3. Instalar dependencias del sistema ---
info "Actualizando el sistema e instalando dependencias (Docker, Docker Compose, Nginx, Certbot)..."
apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common nginx certbot python3-certbot-nginx

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
# Usamos 'echo' en lugar de 'info' porque la función no está disponible en el sub-shell de 'su'
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
    echo 'ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost' >> .env; 
    echo '[INFO] .env creado con valores por defecto. ¡Recuerda cambiarlos si es necesario!'; 
"

# --- 5. Configurar Nginx como proxy inverso ---
info "Configurando Nginx para el dominio $DOMAIN..."

cat > /etc/nginx/sites-available/$DOMAIN << EOL
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/ {
        alias /home/$NEW_USER/project/static/;
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

# --- 6. Obtener certificado SSL con Certbot ---
info "Obteniendo certificado SSL para $DOMAIN..."
# Añadimos --expand para manejar certificados existentes de forma no interactiva
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m $EMAIL --redirect --expand

info "Certificado SSL obtenido e instalado."

# --- 7. Iniciar la aplicación con Docker Compose ---
info "Iniciando la aplicación con Docker Compose..."
su - $NEW_USER -c "
    cd /home/$NEW_USER/project && 
    docker-compose up -d --build
"

info "¡Despliegue completado!"
info "Tu sitio está disponible en https://$DOMAIN"
info "A partir de ahora, gestiona tu aplicación desde el directorio /home/$NEW_USER/project como el usuario '$NEW_USER'."
