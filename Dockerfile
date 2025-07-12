# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y mantener los logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Instalar dependencias del sistema operativo necesarias para algunas librerías de Python
RUN apt-get update && apt-get install -y --no-install-recommends gcc curl netcat-traditional && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Hacer que el script de entrada sea ejecutable
RUN chmod +x /app/entrypoint.sh

# Comando para correr la aplicación
CMD ["sh", "/app/entrypoint.sh"]