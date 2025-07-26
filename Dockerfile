# Usar Python 3.12 como base
FROM python:3.12-slim

# Establecer variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root
RUN useradd --create-home --shell /bin/bash app

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements y instalar dependencias Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . /app/

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles /app/logs \
    && chown -R app:app /app

# Configurar permisos
RUN chmod +x /app/manage_environment.py \
    && chmod +x /app/init-db.sh \
    && chmod +x /app/deploy_server.py \
    && chmod +x /app/debug_docker.py \
    && chmod +x /app/fix_docker.py

# Cambiar a usuario no-root
USER app

# Exponer puerto
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Comando por defecto
CMD ["gunicorn", "blog.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]