# Usar Python 3.12 como base
FROM python:3.12-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles /app/logs

# Hacer ejecutables los scripts
RUN chmod +x /app/gunicorn_config.py /app/start_server.sh /app/monitor_memory.py

# Exponer puerto
EXPOSE 8000

# Comando por defecto usando el script de inicio optimizado
CMD ["/app/start_server.sh"]