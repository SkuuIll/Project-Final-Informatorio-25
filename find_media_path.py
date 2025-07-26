#!/usr/bin/env python3
"""
Script simple para encontrar la ruta de media sin Django.
"""

import os
import sys

def find_media_directory():
    """Encontrar el directorio media del proyecto."""
    print("🔍 Buscando directorio media...")
    
    # Posibles ubicaciones de media
    possible_paths = [
        '/app/media',
        '/app/staticfiles', 
        './media',
        '../media',
        '/home/project/project/media',
        '/var/www/media',
        '/opt/app/media',
    ]
    
    # Buscar en directorio actual y subdirectorios
    current_dir = os.getcwd()
    print(f"📁 Directorio actual: {current_dir}")
    
    # Agregar rutas relativas al directorio actual
    possible_paths.extend([
        os.path.join(current_dir, 'media'),
        os.path.join(current_dir, 'staticfiles'),
        os.path.join(os.path.dirname(current_dir), 'media'),
    ])
    
    found_paths = []
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Encontrado: {path}")
            found_paths.append(path)
            
            # Mostrar contenido
            try:
                contents = os.listdir(path)
                if contents:
                    print(f"   📋 Contenido: {contents[:5]}{'...' if len(contents) > 5 else ''}")
                else:
                    print(f"   📋 Directorio vacío")
            except PermissionError:
                print(f"   ❌ Sin permisos para listar contenido")
        else:
            print(f"❌ No existe: {path}")
    
    # Buscar archivos de configuración Django
    print(f"\n🔍 Buscando archivos de configuración...")
    
    config_files = ['settings.py', 'manage.py', '.env']
    for root, dirs, files in os.walk(current_dir):
        for file in files:
            if file in config_files:
                file_path = os.path.join(root, file)
                print(f"📄 Encontrado: {file_path}")
                
                # Si es settings.py, buscar MEDIA_ROOT
                if file == 'settings.py':
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            if 'MEDIA_ROOT' in content:
                                lines = content.split('\n')
                                for line in lines:
                                    if 'MEDIA_ROOT' in line and not line.strip().startswith('#'):
                                        print(f"   📋 {line.strip()}")
                    except Exception as e:
                        print(f"   ❌ Error leyendo settings: {e}")
    
    return found_paths

def check_current_permissions():
    """Verificar permisos del directorio actual."""
    print(f"\n🔒 Verificando permisos del directorio actual...")
    
    current_dir = os.getcwd()
    
    try:
        # Información del directorio
        stat_info = os.stat(current_dir)
        print(f"📁 Directorio: {current_dir}")
        print(f"🆔 UID: {stat_info.st_uid}, GID: {stat_info.st_gid}")
        
        # Permisos
        import stat
        perms = stat.filemode(stat_info.st_mode)
        print(f"🔒 Permisos: {perms}")
        
        # Verificar acceso
        readable = os.access(current_dir, os.R_OK)
        writable = os.access(current_dir, os.W_OK)
        executable = os.access(current_dir, os.X_OK)
        
        print(f"📖 Legible: {readable}")
        print(f"✏️ Escribible: {writable}")
        print(f"🏃 Ejecutable: {executable}")
        
    except Exception as e:
        print(f"❌ Error verificando permisos: {e}")

def check_user_info():
    """Verificar información del usuario actual."""
    print(f"\n👤 Información del usuario...")
    
    try:
        import pwd
        import grp
        
        # Usuario actual
        uid = os.getuid()
        gid = os.getgid()
        
        user_info = pwd.getpwuid(uid)
        group_info = grp.getgrgid(gid)
        
        print(f"👤 Usuario: {user_info.pw_name} (UID: {uid})")
        print(f"👥 Grupo: {group_info.gr_name} (GID: {gid})")
        print(f"🏠 Home: {user_info.pw_dir}")
        print(f"🐚 Shell: {user_info.pw_shell}")
        
        # Grupos adicionales
        groups = os.getgroups()
        group_names = []
        for group_id in groups:
            try:
                group_names.append(grp.getgrgid(group_id).gr_name)
            except:
                group_names.append(str(group_id))
        
        print(f"👥 Grupos: {', '.join(group_names)}")
        
    except Exception as e:
        print(f"❌ Error obteniendo info de usuario: {e}")

def create_media_directory():
    """Crear directorio media si no existe."""
    print(f"\n📁 Creando directorio media...")
    
    current_dir = os.getcwd()
    media_path = os.path.join(current_dir, 'media')
    
    try:
        if not os.path.exists(media_path):
            os.makedirs(media_path, mode=0o755)
            print(f"✅ Directorio creado: {media_path}")
        else:
            print(f"✅ Directorio ya existe: {media_path}")
        
        # Crear subdirectorios
        subdirs = [
            'ai_posts',
            'ai_posts/content',
            'ai_posts/covers',
            'ai_posts/images',
            'post_images',
            'uploads',
            'images',
        ]
        
        for subdir in subdirs:
            subdir_path = os.path.join(media_path, subdir)
            try:
                if not os.path.exists(subdir_path):
                    os.makedirs(subdir_path, mode=0o755)
                    print(f"✅ Subdirectorio creado: {subdir}")
                else:
                    print(f"✅ Subdirectorio existe: {subdir}")
            except Exception as e:
                print(f"❌ Error creando {subdir}: {e}")
        
        return media_path
        
    except Exception as e:
        print(f"❌ Error creando directorio media: {e}")
        return None

def fix_permissions(media_path):
    """Corregir permisos del directorio media."""
    print(f"\n🔧 Corrigiendo permisos de {media_path}...")
    
    try:
        # Cambiar permisos del directorio principal
        os.chmod(media_path, 0o755)
        print(f"✅ Permisos del directorio principal: 755")
        
        # Cambiar permisos recursivamente
        for root, dirs, files in os.walk(media_path):
            # Permisos de directorios
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    os.chmod(dir_path, 0o755)
                except Exception as e:
                    print(f"❌ Error con directorio {dir_path}: {e}")
            
            # Permisos de archivos
            for file_name in files:
                file_path = os.path.join(root, file_name)
                try:
                    os.chmod(file_path, 0o644)
                except Exception as e:
                    print(f"❌ Error con archivo {file_path}: {e}")
        
        print(f"✅ Permisos corregidos recursivamente")
        
    except Exception as e:
        print(f"❌ Error corrigiendo permisos: {e}")

def main():
    """Función principal."""
    print("🐧 Configuración de media para Ubuntu VPS (sin Django)\n")
    
    # Verificar información del usuario
    check_user_info()
    
    # Verificar permisos actuales
    check_current_permissions()
    
    # Buscar directorio media
    found_paths = find_media_directory()
    
    # Si no se encontró, crear uno
    if not found_paths:
        print(f"\n📁 No se encontró directorio media, creando uno...")
        media_path = create_media_directory()
        if media_path:
            found_paths = [media_path]
    
    # Corregir permisos de los directorios encontrados
    for path in found_paths:
        fix_permissions(path)
    
    print(f"\n🎉 Configuración completada!")
    
    if found_paths:
        print(f"\n📝 Directorios media configurados:")
        for path in found_paths:
            print(f"   📁 {path}")
        
        print(f"\n🔧 Comandos para usar con www-data:")
        for path in found_paths:
            print(f"sudo chown -R www-data:www-data {path}")
            print(f"sudo chmod -R 755 {path}")
    else:
        print(f"\n❌ No se pudo configurar ningún directorio media")

if __name__ == "__main__":
    main()