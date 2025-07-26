#!/bin/bash
set -e

# Script de inicialización de la base de datos PostgreSQL
echo "Inicializando base de datos PostgreSQL..."

# Crear extensiones necesarias
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Crear extensiones útiles
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";
    
    -- Configurar encoding
    UPDATE pg_database SET datcollate='C', datctype='C' WHERE datname='$POSTGRES_DB';
    
    -- Mostrar información de la base de datos
    SELECT version();
    SELECT current_database();
    SELECT current_user;
EOSQL

echo "Base de datos inicializada correctamente."