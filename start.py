#!/usr/bin/env python3
"""
Script de inicio para DevBlog - maneja automáticamente el entorno.
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def is_docker():
    """Detecta si estamos ejecutando en Docker."""
    return os.path.exists('/.dockerenv')

def setup_environment():
    """Configura el entorno automáticamente."""
    if is_docker():
        print("🐳 Detectado entorno Docker")
        # En Docker, usar .env.docker si existe
        docker_env = BASE_DIR / ".env.docker"
        env_file = BASE_DIR / ".env"
        
        if docker_env.exists() and not env_file.exists():
            import shutil
            shutil.copy2(docker_env, env_file)
            print("✅ Configuración Docker aplicada")
    else:
        print("💻 Detectado entorno local")
        # Verificar que esté configurado para desarrollo
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
            
            if 'ENVIRONMENT=production' in content:
                print("⚠️  Detectada configuración de producción en entorno local")
                print("🔧 Cambiando a configuración de desarrollo...")
                
                # Ejecutar script de cambio de entorno
                subprocess.run([sys.executable, "manage_environment.py", "dev"])

def run_migrations():
    """Ejecuta migraciones si es necesario."""
    print("🔄 Verificando migraciones...")
    try:
        result = subprocess.run([
            sys.executable, "manage.py", "migrate", "--check"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("📦 Aplicando migraciones...")
            subprocess.run([sys.executable, "manage.py", "migrate"])
            
            # Inicializar sistema de tags si es la primera vez
            print("🏷️  Inicializando sistema de tags...")
            subprocess.run([
                sys.executable, "manage.py", "initialize_tag_system", 
                "--calculate-cooccurrence", "--create-history"
            ])
        else:
            print("✅ Migraciones al día")
    except Exception as e:
        print(f"⚠️  Error verificando migraciones: {e}")

def start_development_server():
    """Inicia el servidor de desarrollo."""
    print("🚀 Iniciando servidor de desarrollo...")
    print("📍 Servidor disponible en: http://127.0.0.1:8000/")
    print("🛑 Presiona Ctrl+C para detener")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, "manage.py", "runserver"])
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")

def main():
    """Función principal."""
    print("🚀 DevBlog - Sistema de Tags Inteligente")
    print("=" * 50)
    
    # Configurar entorno
    setup_environment()
    
    # Ejecutar migraciones
    run_migrations()
    
    # Iniciar servidor
    if not is_docker():
        start_development_server()
    else:
        print("🐳 En Docker - usar docker-compose para iniciar servicios")

if __name__ == "__main__":
    main()