#!/usr/bin/env python3
"""
Script para debuggear error 500 después de subir video.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

from django.conf import settings
import logging

def check_video_upload_settings():
    """Verificar configuración de subida de videos."""
    print("🎥 Verificando configuración de subida de videos...\n")
    
    # Verificar configuración de archivos
    print("📁 Configuración de archivos:")
    print(f"   MEDIA_ROOT: {getattr(settings, 'MEDIA_ROOT', 'No configurado')}")
    print(f"   MEDIA_URL: {getattr(settings, 'MEDIA_URL', 'No configurado')}")
    print(f"   FILE_UPLOAD_MAX_MEMORY_SIZE: {getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 'Default')}")
    print(f"   DATA_UPLOAD_MAX_MEMORY_SIZE: {getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 'Default')}")
    
    # Verificar límites de tamaño
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440)  # 2.5MB default
    print(f"   Tamaño máximo archivo: {max_size / (1024*1024):.1f}MB")
    
    # Verificar CKEditor configuración
    ckeditor_config = getattr(settings, 'CKEDITOR_5_CONFIGS', {})
    print(f"\n📝 Configuración CKEditor:")
    if ckeditor_config:
        for config_name, config in ckeditor_config.items():
            print(f"   {config_name}:")
            if 'image' in config:
                print(f"     Imágenes: {config['image']}")
            if 'mediaEmbed' in config:
                print(f"     Media embed: {config['mediaEmbed']}")
    else:
        print("   No hay configuración específica de CKEditor")

def check_recent_posts():
    """Verificar posts recientes que puedan tener videos."""
    print("\n📋 Verificando posts recientes...\n")
    
    from posts.models import Post
    
    try:
        recent_posts = Post.objects.order_by('-created_at')[:5]
        
        for post in recent_posts:
            print(f"📄 Post: {post.title[:50]}...")
            print(f"   ID: {post.id}")
            print(f"   Fecha: {post.created_at}")
            print(f"   Autor: {post.author}")
            
            # Verificar si el contenido tiene videos
            if post.content:
                has_video = any(tag in post.content.lower() for tag in ['<video', 'youtube', 'vimeo', 'embed'])
                print(f"   Contiene video: {'Sí' if has_video else 'No'}")
                
                if has_video:
                    print(f"   Contenido (primeros 200 chars): {post.content[:200]}...")
            else:
                print(f"   Sin contenido")
            
            print("-" * 40)
            
    except Exception as e:
        print(f"❌ Error verificando posts: {e}")

def check_media_directory():
    """Verificar directorio media y archivos recientes."""
    print("\n📁 Verificando directorio media...\n")
    
    media_root = getattr(settings, 'MEDIA_ROOT', None)
    if not media_root:
        print("❌ MEDIA_ROOT no configurado")
        return
    
    if not os.path.exists(media_root):
        print(f"❌ Directorio media no existe: {media_root}")
        return
    
    print(f"✅ Directorio media: {media_root}")
    
    # Buscar archivos recientes
    import time
    current_time = time.time()
    recent_files = []
    
    for root, dirs, files in os.walk(media_root):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                file_time = os.path.getmtime(file_path)
                # Archivos de las últimas 24 horas
                if current_time - file_time < 86400:
                    file_size = os.path.getsize(file_path)
                    recent_files.append({
                        'path': file_path,
                        'name': file,
                        'size': file_size,
                        'time': file_time
                    })
            except:
                continue
    
    # Ordenar por fecha (más recientes primero)
    recent_files.sort(key=lambda x: x['time'], reverse=True)
    
    print(f"📊 Archivos recientes (últimas 24h): {len(recent_files)}")
    
    for file_info in recent_files[:10]:  # Mostrar solo los primeros 10
        size_mb = file_info['size'] / (1024 * 1024)
        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_info['time']))
        print(f"   📄 {file_info['name']} - {size_mb:.2f}MB - {time_str}")

def check_django_logs():
    """Verificar configuración de logs de Django."""
    print("\n📝 Configuración de logs...\n")
    
    logging_config = getattr(settings, 'LOGGING', {})
    
    if logging_config:
        print("✅ Configuración de logging encontrada")
        
        # Verificar handlers
        handlers = logging_config.get('handlers', {})
        print(f"📋 Handlers configurados: {list(handlers.keys())}")
        
        # Verificar loggers
        loggers = logging_config.get('loggers', {})
        print(f"📋 Loggers configurados: {list(loggers.keys())}")
        
        # Buscar archivos de log
        for handler_name, handler_config in handlers.items():
            if 'filename' in handler_config:
                log_file = handler_config['filename']
                print(f"📄 Log file ({handler_name}): {log_file}")
                
                if os.path.exists(log_file):
                    try:
                        # Leer últimas líneas del log
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            if lines:
                                print(f"   Últimas 3 líneas:")
                                for line in lines[-3:]:
                                    print(f"     {line.strip()}")
                    except Exception as e:
                        print(f"   ❌ Error leyendo log: {e}")
                else:
                    print(f"   ❌ Archivo de log no existe")
    else:
        print("⚠️ No hay configuración específica de logging")

def suggest_debugging_commands():
    """Sugerir comandos para debugging."""
    print("\n🔧 Comandos para debugging adicional...\n")
    
    print("📋 Para ver logs de error específicos:")
    print("   docker-compose logs -f web | grep -i error")
    print("   docker-compose logs -f web | grep -i exception")
    print("   docker-compose logs -f web | grep -i traceback")
    
    print("\n📋 Para ver logs de Django:")
    print("   docker-compose exec web python manage.py shell")
    print("   >>> import logging")
    print("   >>> logger = logging.getLogger('django')")
    print("   >>> logger.error('Test error')")
    
    print("\n📋 Para verificar configuración:")
    print("   docker-compose exec web python manage.py check")
    print("   docker-compose exec web python manage.py check --deploy")
    
    print("\n📋 Para ver variables de entorno:")
    print("   docker-compose exec web env | grep -E '(DJANGO|DEBUG|MEDIA)'")

def main():
    """Función principal."""
    print("🐛 Debugging Error 500 - Subida de Video\n")
    
    try:
        check_video_upload_settings()
        check_recent_posts()
        check_media_directory()
        check_django_logs()
        suggest_debugging_commands()
        
        print("\n🎯 Posibles causas del error 500:")
        print("   1. Archivo de video demasiado grande")
        print("   2. Formato de video no soportado")
        print("   3. Permisos insuficientes en directorio media")
        print("   4. Error en procesamiento de CKEditor")
        print("   5. Límites de memoria excedidos")
        
        print("\n💡 Próximos pasos:")
        print("   1. Ejecutar: docker-compose logs -f web | grep -i error")
        print("   2. Verificar tamaño del video subido")
        print("   3. Revisar permisos del directorio media")
        print("   4. Comprobar configuración de CKEditor")
        
    except Exception as e:
        print(f"\n❌ Error durante el debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()