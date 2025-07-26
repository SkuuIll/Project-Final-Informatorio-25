#!/usr/bin/env python3
"""
Prueba específica de eliminación en VPS.
"""

import os
import sys
import django
from PIL import Image
from io import BytesIO

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

from django.core.files.storage import default_storage
from posts.media_image_selector import MediaImageSelector

def create_test_image():
    """Crear imagen de prueba para eliminar."""
    print("🎨 Creando imagen de prueba...")
    
    # Crear imagen
    img = Image.new('RGB', (400, 400), color='blue')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    
    # Guardar en storage
    test_path = 'vps_test_deletion.jpg'
    saved_path = default_storage.save(test_path, buffer)
    
    print(f"✅ Imagen creada: {saved_path}")
    
    # Verificar permisos del archivo creado
    if hasattr(default_storage, 'path'):
        full_path = default_storage.path(saved_path)
        if os.path.exists(full_path):
            import stat
            file_stat = os.stat(full_path)
            perms = stat.filemode(file_stat.st_mode)
            print(f"🔒 Permisos del archivo: {perms}")
            
            # Verificar propietario
            try:
                import pwd, grp
                owner = pwd.getpwuid(file_stat.st_uid).pw_name
                group = grp.getgrgid(file_stat.st_gid).gr_name
                print(f"👤 Propietario: {owner}:{group}")
            except:
                print(f"👤 Propietario: UID {file_stat.st_uid}, GID {file_stat.st_gid}")
    
    return saved_path

def test_deletion(image_path):
    """Probar eliminación de imagen."""
    print(f"\n🗑️ Probando eliminación de: {image_path}")
    
    # Verificar que existe
    if not default_storage.exists(image_path):
        print(f"❌ La imagen no existe")
        return False
    
    print(f"✅ Imagen existe en storage")
    
    # Intentar eliminar
    success, message = MediaImageSelector.delete_image(image_path)
    
    if success:
        print(f"✅ Eliminación exitosa: {message}")
        
        # Verificar que se eliminó
        if not default_storage.exists(image_path):
            print(f"✅ Confirmado: Imagen eliminada del storage")
            return True
        else:
            print(f"❌ Error: Imagen aún existe en storage")
            return False
    else:
        print(f"❌ Error en eliminación: {message}")
        return False

def test_existing_image():
    """Probar con imagen existente."""
    print(f"\n🔍 Probando con imagen existente...")
    
    images = MediaImageSelector.get_all_media_images()
    
    if not images:
        print(f"❌ No hay imágenes existentes")
        return False
    
    # Buscar imagen de prueba o usar la primera
    test_image = None
    for img in images:
        if 'test' in img['filename'].lower() or 'sample' in img['filename'].lower():
            test_image = img
            break
    
    if not test_image:
        test_image = images[0]
    
    print(f"🎯 Imagen seleccionada: {test_image['filename']}")
    print(f"📁 Ruta: {test_image['path']}")
    
    # Verificar permisos
    if hasattr(default_storage, 'path'):
        full_path = default_storage.path(test_image['path'])
        if os.path.exists(full_path):
            import stat
            file_stat = os.stat(full_path)
            perms = stat.filemode(file_stat.st_mode)
            print(f"🔒 Permisos: {perms}")
            
            writable = os.access(full_path, os.W_OK)
            print(f"✏️ Escribible: {writable}")
            
            if not writable:
                print(f"⚠️ Archivo no es escribible por el usuario actual")
    
    # Confirmar eliminación
    confirm = input(f"❓ ¿Eliminar '{test_image['filename']}'? (s/N): ")
    if confirm.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        return test_deletion(test_image['path'])
    else:
        print(f"❌ Eliminación cancelada")
        return False

def check_media_permissions():
    """Verificar permisos del directorio media."""
    print(f"\n🔒 Verificando permisos del directorio media...")
    
    if hasattr(default_storage, 'location'):
        media_path = default_storage.location
        print(f"📁 Directorio media: {media_path}")
        
        if os.path.exists(media_path):
            import stat
            media_stat = os.stat(media_path)
            perms = stat.filemode(media_stat.st_mode)
            print(f"🔒 Permisos: {perms}")
            
            # Verificar propietario
            try:
                import pwd, grp
                owner = pwd.getpwuid(media_stat.st_uid).pw_name
                group = grp.getgrgid(media_stat.st_gid).gr_name
                print(f"👤 Propietario: {owner}:{group}")
            except:
                print(f"👤 Propietario: UID {media_stat.st_uid}, GID {media_stat.st_gid}")
            
            # Verificar acceso
            readable = os.access(media_path, os.R_OK)
            writable = os.access(media_path, os.W_OK)
            executable = os.access(media_path, os.X_OK)
            
            print(f"📖 Legible: {readable}")
            print(f"✏️ Escribible: {writable}")
            print(f"🏃 Ejecutable: {executable}")
            
            if not writable:
                print(f"⚠️ Directorio media no es escribible")
                print(f"💡 Ejecuta: sudo chown -R www-data:www-data {media_path}")
        else:
            print(f"❌ Directorio media no existe: {media_path}")

def main():
    """Función principal."""
    print("🧪 Prueba de eliminación en VPS\n")
    
    try:
        # Verificar permisos del directorio media
        check_media_permissions()
        
        # Crear y probar eliminación de imagen nueva
        print(f"\n" + "="*50)
        print(f"PRUEBA 1: Imagen nueva")
        test_path = create_test_image()
        success1 = test_deletion(test_path)
        
        # Probar con imagen existente
        print(f"\n" + "="*50)
        print(f"PRUEBA 2: Imagen existente")
        success2 = test_existing_image()
        
        # Resumen
        print(f"\n🎉 Resumen de pruebas:")
        print(f"   • Imagen nueva: {'✅ OK' if success1 else '❌ FALLO'}")
        print(f"   • Imagen existente: {'✅ OK' if success2 else '❌ FALLO'}")
        
        if success1 and success2:
            print(f"\n✅ ¡Eliminación funciona correctamente en VPS!")
        elif success1:
            print(f"\n⚠️ Eliminación funciona para imágenes nuevas")
            print(f"💡 Verifica permisos de imágenes existentes")
        else:
            print(f"\n❌ Eliminación no funciona")
            print(f"💡 Verifica:")
            print(f"   1. Permisos del directorio media")
            print(f"   2. Propietario www-data")
            print(f"   3. AppArmor (si está activo)")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()