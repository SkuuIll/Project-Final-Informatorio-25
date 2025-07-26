#!/usr/bin/env python3
"""
Script de utilidad para gestionar entornos de desarrollo y producción.
"""

import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def switch_to_development():
    """Cambia al entorno de desarrollo local."""
    print("🔧 Cambiando a entorno de desarrollo...")
    
    # Copiar .env para desarrollo
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        print("✅ Archivo .env ya configurado para desarrollo")
    else:
        print("❌ Archivo .env no encontrado")
        return False

def switch_to_minimal():
    """Cambia al entorno mínimo (solo tags inteligentes, sin IA)."""
    print("⚡ Cambiando a entorno mínimo...")
    
    # Verificar que existe .env.minimal
    minimal_env = BASE_DIR / ".env.minimal"
    if not minimal_env.exists():
        print("❌ Archivo .env.minimal no encontrado")
        return False
    
    # Copiar .env.minimal a .env
    env_file = BASE_DIR / ".env"
    shutil.copy2(minimal_env, env_file)
    print("✅ Archivo .env.minimal copiado a .env")
    
    print("🎉 Entorno mínimo configurado correctamente")
    print("📝 Configuración:")
    print("   - Base de datos: SQLite")
    print("   - Caché: Memoria local")
    print("   - IA: Deshabilitada")
    print("   - Tags: Sistema inteligente activo")
    print("   - Debug: True")
    return True
    
    # Verificar configuración
    with open(env_file, 'r') as f:
        content = f.read()
        if 'ENVIRONMENT=development' in content:
            print("✅ Variable ENVIRONMENT configurada para development")
        else:
            # Agregar o actualizar ENVIRONMENT
            if 'ENVIRONMENT=' in content:
                content = content.replace('ENVIRONMENT=production', 'ENVIRONMENT=development')
            else:
                content += '\nENVIRONMENT=development\n'
            
            with open(env_file, 'w') as f:
                f.write(content)
            print("✅ Variable ENVIRONMENT actualizada a development")
    
    print("🎉 Entorno de desarrollo configurado correctamente")
    print("📝 Configuración:")
    print("   - Base de datos: SQLite")
    print("   - Caché: Memoria local")
    print("   - Celery: Síncrono (EAGER)")
    print("   - Debug: True")
    return True

def switch_to_production():
    """Cambia al entorno de producción/Docker."""
    print("🚀 Cambiando a entorno de producción...")
    
    # Verificar que existe .env.docker
    docker_env = BASE_DIR / ".env.docker"
    if not docker_env.exists():
        print("❌ Archivo .env.docker no encontrado")
        return False
    
    # Copiar .env.docker a .env
    env_file = BASE_DIR / ".env"
    shutil.copy2(docker_env, env_file)
    print("✅ Archivo .env.docker copiado a .env")
    
    print("🎉 Entorno de producción configurado correctamente")
    print("📝 Configuración:")
    print("   - Base de datos: PostgreSQL")
    print("   - Caché: Redis")
    print("   - Celery: Redis broker")
    print("   - Debug: False")
    return True

def show_current_environment():
    """Muestra el entorno actual."""
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        return
    
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Detectar entorno
    if 'ENVIRONMENT=development' in content:
        env = "🔧 Desarrollo Local"
        db = "SQLite"
        cache = "Memoria local"
        debug = "True"
    elif 'ENVIRONMENT=production' in content:
        env = "🚀 Producción/Docker"
        db = "PostgreSQL"
        cache = "Redis"
        debug = "False"
    else:
        env = "❓ No definido"
        db = "Desconocido"
        cache = "Desconocido"
        debug = "Desconocido"
    
    print(f"📊 Entorno actual: {env}")
    print(f"   - Base de datos: {db}")
    print(f"   - Caché: {cache}")
    print(f"   - Debug: {debug}")

def check_docker_environment():
    """Verifica si estamos ejecutando en Docker."""
    if os.path.exists('/.dockerenv'):
        print("🐳 Ejecutándose dentro de Docker")
        return True
    else:
        print("💻 Ejecutándose en sistema local")
        return False

def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("🔧 Gestor de Entornos - DevBlog")
        print("=" * 40)
        print("Uso: python manage_environment.py [comando]")
        print()
        print("Comandos disponibles:")
        print("  dev        - Cambiar a entorno de desarrollo")
        print("  minimal    - Cambiar a entorno mínimo (sin IA)")
        print("  prod       - Cambiar a entorno de producción")
        print("  status     - Mostrar entorno actual")
        print("  check      - Verificar si está en Docker")
        print()
        show_current_environment()
        return
    
    command = sys.argv[1].lower()
    
    if command in ['dev', 'development']:
        switch_to_development()
    elif command in ['minimal', 'min']:
        switch_to_minimal()
    elif command in ['prod', 'production']:
        switch_to_production()
    elif command in ['status', 'current']:
        show_current_environment()
    elif command in ['check', 'docker']:
        check_docker_environment()
    else:
        print(f"❌ Comando desconocido: {command}")
        print("Usa 'python manage_environment.py' para ver la ayuda")

if __name__ == "__main__":
    main()