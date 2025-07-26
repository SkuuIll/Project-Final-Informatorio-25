#!/usr/bin/env python3
"""
Diagnóstico rápido del VPS sin dependencias.
"""

import os
import sys

def main():
    print("🔍 Diagnóstico rápido del VPS\n")
    
    # Información básica
    print(f"📁 Directorio actual: {os.getcwd()}")
    print(f"👤 Usuario: {os.getenv('USER', 'unknown')}")
    print(f"🐍 Python: {sys.version}")
    
    # Buscar archivos del proyecto
    files_to_find = ['manage.py', 'requirements.txt', 'settings.py']
    print(f"\n📋 Archivos del proyecto:")
    for file in files_to_find:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            # Buscar en subdirectorios
            found = False
            for root, dirs, files in os.walk('.'):
                if file in files:
                    print(f"✅ {file} (en {root})")
                    found = True
                    break
            if not found:
                print(f"❌ {file}")
    
    # Buscar directorios importantes
    dirs_to_find = ['media', 'static', 'staticfiles', 'venv', 'env']
    print(f"\n📁 Directorios importantes:")
    for dir_name in dirs_to_find:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
            # Mostrar contenido si es media
            if dir_name in ['media', 'staticfiles']:
                try:
                    contents = os.listdir(dir_name)
                    print(f"   📋 Contenido: {contents[:3]}{'...' if len(contents) > 3 else ''}")
                except:
                    print(f"   ❌ Sin permisos para listar")
        else:
            print(f"❌ {dir_name}/")
    
    # Verificar permisos del directorio actual
    print(f"\n🔒 Permisos del directorio actual:")
    try:
        readable = os.access('.', os.R_OK)
        writable = os.access('.', os.W_OK)
        executable = os.access('.', os.X_OK)
        
        print(f"📖 Legible: {readable}")
        print(f"✏️ Escribible: {writable}")
        print(f"🏃 Ejecutable: {executable}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Comandos sugeridos
    print(f"\n💡 Comandos sugeridos:")
    print(f"# Encontrar entorno virtual:")
    print(f"find . -name 'activate' -type f 2>/dev/null")
    print(f"")
    print(f"# Activar entorno virtual (ejemplo):")
    print(f"source venv/bin/activate")
    print(f"")
    print(f"# Verificar Django:")
    print(f"python -c 'import django; print(django.VERSION)'")
    print(f"")
    print(f"# Crear directorio media:")
    print(f"mkdir -p media/ai_posts/{{content,covers,images}}")
    print(f"mkdir -p media/{{post_images,uploads,images}}")

if __name__ == "__main__":
    main()