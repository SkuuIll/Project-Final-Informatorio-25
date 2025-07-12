# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Evitar que Python escriba archivos .pyc y mantener los logs sin buffer
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instalar dependencias del sistema operativo necesarias para algunas librerías de Python
# Por ejemplo, libpq-dev es necesaria para psycopg2 (PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de requerimientos e instalar las dependencias de Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install Cython && pip install -r requirements.txt

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto 8000 para que podamos acceder a la aplicación
EXPOSE 8000

# Comando para correr la aplicación
# Nota: Para producción real, se recomienda usar un servidor WSGI como Gunicorn en lugar del servidor de desarrollo de Django.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]