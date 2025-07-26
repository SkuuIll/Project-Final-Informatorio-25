#!/usr/bin/env python3
"""
Script para gestionar imágenes en la carpeta media.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

from posts.media_image_selector import MediaImageSelector

def list_all_images():
    """Listar todas las imágenes en media."""
    print("📋 Listando todas las imágenes en media...")
    
    images = MediaImageSelector.get_all_media_images()
    stats = MediaImageSelector.get_image_stats()
    
    print(f"\n📊 Resumen:")
    print(f"   • Total de imágenes: {stats['total_images']}")
    print(f"   • Tamaño total: {stats['total_size_mb']}MB")
    print(f"   • Carpetas: {len(stats['by_folder'])}")
    
    print(f"\n📁 Por carpetas:")
    for folder, count in stats['by_folder'].items():
        print(f"   • {folder}: {count} imágenes")
    
    if len(images) > 0:
        print(f"\n📋 Últimas 10 imágenes:")
        for i, img in enumerate(images[:10], 1):
            date_str = datetime.fromtimestamp(img['modified_time']).strftime('%d/%m/%Y %H:%M') if img['modified_time'] else 'Sin fecha'
            print(f"   {i:2d}. {img['filename']} ({img['folder']}) - {img['size_mb']}MB - {date_str}")

def clean_test_images():
    """Limpiar imágenes de prueba."""
    print("🧹 Limpiando imágenes de prueba...")
    
    # Patrones de archivos de prueba
    test_patterns = [
        'extracted_',
        'cover_',
        'ai_generated_',
        'manual_upload_',
        'user_photo',
        'logo_placeholder',
        'banner_sample'
    ]
    
    images = MediaImageSelector.get_all_media_images()
    test_images = []
    
    for img in images:
        filename = img['filename'].lower()
        if any(pattern in filename for pattern in test_patterns):
            test_images.append(img['path'])
    
    if not test_images:
        print("✅ No se encontraron imágenes de prueba para limpiar.")
        return
    
    print(f"🗑️ Se encontraron {len(test_images)} imágenes de prueba:")
    for path in test_images:
        print(f"   • {path}")
    
    confirm = input(f"\n❓ ¿Eliminar estas {len(test_images)} imágenes? (s/N): ")
    if confirm.lower() in ['s', 'si', 'sí', 'y', 'yes']:
        result = MediaImageSelector.bulk_delete_images(test_images)
        print(f"✅ Eliminadas {result['deleted_count']} imágenes de prueba")
        if result['errors']:
            print(f"❌ Errores: {len(result['errors'])}")
            for error in result['errors'][:5]:  # Mostrar solo los primeros 5 errores
                print(f"   • {error}")
    else:
        print("❌ Operación cancelada")

def find_large_images(min_size_mb=1.0):
    """Encontrar imágenes grandes."""
    print(f"🔍 Buscando imágenes mayores a {min_size_mb}MB...")
    
    images = MediaImageSelector.get_all_media_images()
    large_images = [img for img in images if img['size_mb'] >= min_size_mb]
    
    if not large_images:
        print(f"✅ No se encontraron imágenes mayores a {min_size_mb}MB")
        return
    
    print(f"📊 Se encontraron {len(large_images)} imágenes grandes:")
    total_size = sum(img['size_mb'] for img in large_images)
    
    for img in sorted(large_images, key=lambda x: x['size_mb'], reverse=True):
        print(f"   • {img['filename']} ({img['folder']}) - {img['size_mb']}MB")
    
    print(f"\n💾 Tamaño total de imágenes grandes: {total_size:.2f}MB")

def find_old_images(days=30):
    """Encontrar imágenes antiguas."""
    print(f"🕒 Buscando imágenes más antiguas que {days} días...")
    
    images = MediaImageSelector.get_all_media_images()
    cutoff_time = (datetime.now() - timedelta(days=days)).timestamp()
    
    old_images = [img for img in images if img['modified_time'] and img['modified_time'] < cutoff_time]
    
    if not old_images:
        print(f"✅ No se encontraron imágenes más antiguas que {days} días")
        return
    
    print(f"📊 Se encontraron {len(old_images)} imágenes antiguas:")
    total_size = sum(img['size_mb'] for img in old_images)
    
    for img in sorted(old_images, key=lambda x: x['modified_time']):
        date_str = datetime.fromtimestamp(img['modified_time']).strftime('%d/%m/%Y')
        print(f"   • {img['filename']} ({img['folder']}) - {date_str}")
    
    print(f"\n💾 Tamaño total de imágenes antiguas: {total_size:.2f}MB")

def search_images(query):
    """Buscar imágenes por nombre."""
    print(f"🔍 Buscando imágenes que contengan '{query}'...")
    
    results = MediaImageSelector.search_images(query)
    
    if not results:
        print(f"❌ No se encontraron imágenes que contengan '{query}'")
        return
    
    print(f"📊 Se encontraron {len(results)} resultados:")
    for img in results:
        date_str = datetime.fromtimestamp(img['modified_time']).strftime('%d/%m/%Y') if img['modified_time'] else 'Sin fecha'
        print(f"   • {img['filename']} ({img['folder']}) - {img['size_mb']}MB - {date_str}")

def show_folder_details(folder_name):
    """Mostrar detalles de una carpeta específica."""
    print(f"📁 Detalles de la carpeta '{folder_name}'...")
    
    images = MediaImageSelector.get_all_media_images(folder_name)
    
    if not images:
        print(f"❌ No se encontraron imágenes en '{folder_name}'")
        return
    
    total_size = sum(img['size_mb'] for img in images)
    print(f"📊 Carpeta '{folder_name}':")
    print(f"   • Imágenes: {len(images)}")
    print(f"   • Tamaño total: {total_size:.2f}MB")
    print(f"   • Tamaño promedio: {total_size/len(images):.2f}MB")
    
    print(f"\n📋 Archivos:")
    for img in images:
        date_str = datetime.fromtimestamp(img['modified_time']).strftime('%d/%m/%Y %H:%M') if img['modified_time'] else 'Sin fecha'
        print(f"   • {img['filename']} - {img['size_mb']}MB - {date_str}")

def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("🗂️ Gestor de Imágenes Media")
        print("\nUso:")
        print("  python manage_media_images.py list                    # Listar todas las imágenes")
        print("  python manage_media_images.py clean                   # Limpiar imágenes de prueba")
        print("  python manage_media_images.py large [size_mb]         # Encontrar imágenes grandes")
        print("  python manage_media_images.py old [days]              # Encontrar imágenes antiguas")
        print("  python manage_media_images.py search <query>          # Buscar imágenes")
        print("  python manage_media_images.py folder <folder_name>    # Detalles de carpeta")
        return
    
    command = sys.argv[1].lower()
    
    try:
        if command == 'list':
            list_all_images()
        elif command == 'clean':
            clean_test_images()
        elif command == 'large':
            size_mb = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
            find_large_images(size_mb)
        elif command == 'old':
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            find_old_images(days)
        elif command == 'search':
            if len(sys.argv) < 3:
                print("❌ Debes proporcionar un término de búsqueda")
                return
            search_images(sys.argv[2])
        elif command == 'folder':
            if len(sys.argv) < 3:
                print("❌ Debes proporcionar un nombre de carpeta")
                return
            show_folder_details(sys.argv[2])
        else:
            print(f"❌ Comando desconocido: {command}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()