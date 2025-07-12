#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Script de Instalación Mejorado para DevBlog en Ubuntu ---

echo "Iniciando la instalación de DevBlog..."

# 1. Actualizar lista de paquetes e instalar prerrequisitos
echo "-> Actualizando paquetes e instalando prerrequisitos..."
sudo apt-get update -y
sudo apt-get install -y git ca-certificates curl

# 2. Instalar Docker Engine y Docker Compose (Método oficial de Docker)
echo "-> Configurando el repositorio de Docker e instalando Docker Engine..."

# Añadir la clave GPG oficial de Docker
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Añadir el repositorio a las fuentes de Apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update -y

# Instalar los paquetes de Docker
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "-> Docker instalado correctamente."

# 3. Añadir usuario al grupo de Docker para evitar usar sudo
echo "-> Añadiendo el usuario actual al grupo de Docker..."
sudo usermod -aG docker $USER
echo "¡Importante! Debes cerrar sesión y volver a iniciarla o ejecutar 'newgrp docker' para que los cambios en el grupo de Docker surtan efecto."

# 4. Clonar el repositorio
echo "-> Clonando el repositorio del proyecto..."
# Clonar solo si el directorio no existe
if [ ! -d "Project-Final-Informatorio-25" ]; then
    git clone https://github.com/SkuuIll/Project-Final-Informatorio-25.git
else
    echo "El directorio del proyecto ya existe, omitiendo la clonación."
fi
cd Project-Final-Informatorio-25

# 5. Construir y ejecutar los contenedores de Docker
# Nota: No es necesario instalar dependencias de Python en el host.
# El Dockerfile se encarga de eso dentro del contenedor.
echo "-> Construyendo y ejecutando los contenedores de Docker con docker compose..."
# Usar 'docker compose' (con espacio), que es el nuevo comando del plugin
docker compose up -d --build

echo ""
echo "--- ¡Instalación completada! ---"
echo "La aplicación debería estar ejecutándose en segundo plano."
echo "Puedes acceder a ella en tu navegador en: http://localhost:8000"
echo "Para verificar el estado, usa: docker compose ps"
echo "Para ver los logs, usa: docker compose logs -f web"
echo "Para detener la aplicación, usa: docker compose down"