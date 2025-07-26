#!/usr/bin/env python3
"""
Script para configurar permisos correctos en Ubuntu VPS.
"""

import os
import sys
import django
import stat
import subprocess

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

from django.core.files.storage import default_storage
from django.conf import settings

def check_and_fix_media_permissions():
    """Verificar y corregir permisos del directorio media."""
    print("🔧 Configurando permisos para Ubuntu VPS...")
    
    if not hasattr(default_storage, 'location'):
        print("❌ Storage no es FileSystemStorage, no se pueden configurar permisos")
        return False
    
    media_path = default_storage.location
    print(f"📁 Directorio media: {media_path}")
    
    if not os.path.exists(media_path):
        print(f"❌ Directorio media no existe: {media_path}")
        return False
    
    try:
        # Verificar permisos actuales
        media_stat = os.stat(media_path)
        current_perms = stat.filemode(media_stat.st_mode)
        print(f"🔒 Permisos actuales: {current_perms}")
        
        # Verificar si es escribible
        if not os.access(media_path, os.W_OK):
            print("⚠️ Directorio media no es escribible")
            
            # Intentar corregir permisos
            try:
                print("🔧 Intentando corregir permisos del directorio...")
                os.chmod(media_path, 0o755)
                print("✅ Permisos del directorio cambiados a 755")
            except PermissionError:
                print("❌ No se pueden cambiar permisos (requiere sudo)")
                print("💡 Ejecuta manualmente: sudo chmod 755 " + media_path)
                return False
        
        # Corregir permisos de archivos existentes
        print("🔧 Corrigiendo permisos de archivos existentes...")
        fixed_count = 0
        error_count = 0
        
        for root, dirs, files in os.walk(media_path):
            # Corregir permisos de directorios
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    os.chmod(dir_path, 0o755)
                    fixed_count += 1
                except Exception as e:
                    print(f"❌ Error con directorio {dir_path}: {e}")
                    error_count += 1
            
            # Corregir permisos de archivos
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    os.chmod(file_path, 0o644)
                    fixed_count += 1
                except Exception as e:
                    print(f"❌ Error con archivo {file_path}: {e}")
                    error_count += 1
        
        print(f"✅ Permisos corregidos: {fixed_count} elementos")
        if error_count > 0:
            print(f"❌ Errores: {error_count} elementos")
        
        return error_count == 0
        
    except Exception as e:
        print(f"❌ Error configurando permisos: {e}")
        return False

def create_media_subdirectories():
    """Crear subdirectorios necesarios con permisos correctos."""
    print("\n📁 Creando subdirectorios necesarios...")
    
    subdirs = [
        'ai_posts',
        'ai_posts/content',
        'ai_posts/covers',
        'ai_posts/images',
        'post_images',
        'uploads',
        'images',
    ]
    
    created_count = 0
    
    for subdir in subdirs:
        try:
            if not default_storage.exists(subdir):
                # Crear directorio usando os.makedirs para mejor control
                if hasattr(default_storage, 'location'):
                    full_path = os.path.join(default_storage.location, subdir)
                    os.makedirs(full_path, mode=0o755, exist_ok=True)
                    print(f"✅ Creado: {subdir}")
                    created_count += 1
                else:
                    print(f"⚠️ No se puede crear {subdir} (storage no es filesystem)")
            else:
                print(f"✅ Ya existe: {subdir}")
        except Exception as e:
            print(f"❌ Error creando {subdir}: {e}")
    
    print(f"📊 Directorios creados: {created_count}")

def check_web_server_user():
    """Verificar usuario del servidor web."""
    print("\n👤 Verificando usuario del servidor web...")
    
    # Usuarios comunes de servidor web
    web_users = ['www-data', 'nginx', 'apache', 'httpd']
    
    current_user = os.getenv('USER', 'unknown')
    print(f"👤 Usuario actual: {current_user}")
    
    # Verificar si algún usuario web existe
    for user in web_users:
        try:
            result = subprocess.run(['id', user], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Usuario web encontrado: {user}")
                
                # Sugerir cambio de propietario
                if hasattr(default_storage, 'location'):
                    media_path = default_storage.location
                    print(f"💡 Considera ejecutar: sudo chown -R {user}:{user} {media_path}")
                
                return user
        except Exception:
            continue
    
    print("⚠️ No se encontró usuario web estándar")
    return None

def generate_nginx_config():
    """Generar configuración de ejemplo para Nginx."""
    print("\n🌐 Generando configuración de ejemplo para Nginx...")
    
    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    media_root = getattr(settings, 'MEDIA_ROOT', '/path/to/media')
    
    nginx_config = f"""
# Configuración de Nginx para archivos media
location {media_url} {{
    alias {media_root};
    expires 1y;
    add_header Cache-Control "public, immutable";
    
    # Permitir eliminación de archivos (para la galería)
    dav_methods DELETE;
    dav_access user:rw group:rw all:r;
}}

# Configuración de permisos para Django
location /image-gallery/ {{
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}}
"""
    
    print("📝 Configuración de Nginx sugerida:")
    print(nginx_config)
    
    # Guardar en archivo
    try:
        with open('nginx_media_config.txt', 'w') as f:
            f.write(nginx_config)
        print("✅ Configuración guardada en: nginx_media_config.txt")
    except Exception as e:
        print(f"❌ Error guardando configuración: {e}")

def check_selinux_apparmor():
    """Verificar SELinux/AppArmor que pueden interferir."""
    print("\n🛡️ Verificando SELinux/AppArmor...")
    
    # Verificar SELinux
    try:
        result = subprocess.run(['getenforce'], capture_output=True, text=True)
        if result.returncode == 0:
            selinux_status = result.stdout.strip()
            print(f"🛡️ SELinux: {selinux_status}")
            
            if selinux_status == 'Enforcing':
                print("⚠️ SELinux está activo, puede interferir con eliminación de archivos")
                print("💡 Considera: sudo setsebool -P httpd_can_network_connect 1")
                print("💡 O configurar contextos SELinux apropiados")
        else:
            print("✅ SELinux no detectado")
    except FileNotFoundError:
        print("✅ SELinux no instalado")
    except Exception as e:
        print(f"❌ Error verificando SELinux: {e}")
    
    # Verificar AppArmor
    try:
        result = subprocess.run(['aa-status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("🛡️ AppArmor está activo")
            print("⚠️ Puede interferir con operaciones de archivos")
            print("💡 Verifica perfiles de AppArmor para tu aplicación web")
        else:
            print("✅ AppArmor no activo")
    except FileNotFoundError:
        print("✅ AppArmor no instalado")
    except Exception as e:
        print(f"❌ Error verificando AppArmor: {e}")

def main():
    """Función principal."""
    print("🐧 Configuración de permisos para Ubuntu VPS\n")
    
    try:
        # Verificar y corregir permisos
        perms_ok = check_and_fix_media_permissions()
        
        # Crear subdirectorios
        create_media_subdirectories()
        
        # Verificar usuario web
        web_user = check_web_server_user()
        
        # Generar configuración de Nginx
        generate_nginx_config()
        
        # Verificar seguridad
        check_selinux_apparmor()
        
        print("\n🎉 Configuración completada!")
        
        if perms_ok:
            print("✅ Permisos configurados correctamente")
        else:
            print("⚠️ Algunos permisos requieren intervención manual")
        
        print("\n📝 Pasos adicionales recomendados:")
        print("1. Verificar que el usuario web tenga acceso al directorio media")
        print("2. Reiniciar el servidor web después de cambios de permisos")
        print("3. Probar eliminación desde la galería web")
        print("4. Verificar logs del servidor web para errores de permisos")
        
        if web_user:
            media_path = getattr(default_storage, 'location', '/path/to/media')
            print(f"\n🔧 Comandos útiles:")
            print(f"sudo chown -R {web_user}:{web_user} {media_path}")
            print(f"sudo chmod -R 755 {media_path}")
            print(f"sudo find {media_path} -type f -exec chmod 644 {{}} \\;")
        
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()