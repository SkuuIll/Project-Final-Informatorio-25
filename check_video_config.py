#!/usr/bin/env python3
"""
Script para verificar configuración de videos en CKEditor.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

from django.conf import settings

def check_ckeditor_config():
    """Verificar configuración de CKEditor para videos."""
    print("📝 Verificando configuración de CKEditor...\n")
    
    # Verificar configuración de CKEditor 5
    ckeditor_configs = getattr(settings, 'CKEDITOR_5_CONFIGS', {})
    
    if not ckeditor_configs:
        print("❌ No hay configuración de CKEDITOR_5_CONFIGS")
        return
    
    for config_name, config in ckeditor_configs.items():
        print(f"⚙️ Configuración: {config_name}")
        
        # Verificar toolbar
        toolbar = config.get('toolbar', [])
        print(f"   🔧 Toolbar: {toolbar}")
        
        # Verificar si hay soporte para media/video
        has_media = any('media' in str(item).lower() or 'video' in str(item).lower() for item in toolbar)
        print(f"   🎥 Soporte media/video: {'Sí' if has_media else 'No'}")
        
        # Verificar configuración específica de media
        if 'mediaEmbed' in config:
            print(f"   📺 MediaEmbed config: {config['mediaEmbed']}")
        
        # Verificar configuración de imagen (puede afectar videos)
        if 'image' in config:
            print(f"   🖼️ Image config: {config['image']}")
        
        print()

def check_file_upload_limits():
    """Verificar límites de subida de archivos."""
    print("📁 Verificando límites de subida...\n")
    
    # Límites de Django
    max_memory = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440)
    max_data = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 2621440)
    
    print(f"📊 Límites de Django:")
    print(f"   FILE_UPLOAD_MAX_MEMORY_SIZE: {max_memory / (1024*1024):.1f}MB")
    print(f"   DATA_UPLOAD_MAX_MEMORY_SIZE: {max_data / (1024*1024):.1f}MB")
    
    # Verificar configuración de Nginx (si existe)
    print(f"\n🌐 Configuración recomendada para Nginx:")
    print(f"   client_max_body_size 100M;")
    print(f"   client_body_timeout 60s;")
    print(f"   client_header_timeout 60s;")

def check_media_types():
    """Verificar tipos de media soportados."""
    print("\n🎬 Tipos de media comúnmente soportados...\n")
    
    video_formats = [
        'mp4', 'webm', 'ogg', 'avi', 'mov', 'wmv', 'flv', 'm4v'
    ]
    
    print("📹 Formatos de video:")
    for fmt in video_formats:
        print(f"   • .{fmt}")
    
    print("\n🔗 Embeds soportados por CKEditor:")
    embed_providers = [
        'YouTube', 'Vimeo', 'Dailymotion', 'Spotify', 'Instagram', 'Twitter', 'Facebook'
    ]
    
    for provider in embed_providers:
        print(f"   • {provider}")

def suggest_video_config():
    """Sugerir configuración para videos."""
    print("\n⚙️ Configuración recomendada para videos...\n")
    
    print("📝 En settings.py:")
    print("""
# Aumentar límites para videos
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB

# Configuración de CKEditor 5 con soporte para videos
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': [
            'heading', '|', 'bold', 'italic', 'link',
            'bulletedList', 'numberedList', 'blockQuote', 'imageUpload',
            'mediaEmbed', '|', 'undo', 'redo'  # ← mediaEmbed para videos
        ],
        'mediaEmbed': {
            'previewsInData': True,
            'providers': [
                {
                    'name': 'youtube',
                    'url': r'youtube\.com/watch\?v=([\w-]+)',
                    'html': '<iframe src="https://www.youtube.com/embed/{0}" frameborder="0" allowfullscreen></iframe>'
                },
                {
                    'name': 'vimeo', 
                    'url': r'vimeo\.com/(\d+)',
                    'html': '<iframe src="https://player.vimeo.com/video/{0}" frameborder="0" allowfullscreen></iframe>'
                }
            ]
        }
    }
}
""")
    
    print("\n🐳 En docker-compose.yml:")
    print("""
services:
  web:
    environment:
      - DJANGO_FILE_UPLOAD_MAX_SIZE=104857600  # 100MB
    volumes:
      - ./media:/app/media  # Asegurar que media esté montado
""")
    
    print("\n🌐 En nginx.conf:")
    print("""
server {
    client_max_body_size 100M;
    client_body_timeout 60s;
    
    location /media/ {
        alias /path/to/media/;
        expires 1y;
    }
}
""")

def main():
    """Función principal."""
    print("🎥 Verificación de Configuración de Videos\n")
    
    try:
        check_ckeditor_config()
        check_file_upload_limits()
        check_media_types()
        suggest_video_config()
        
        print("\n🔍 Para diagnosticar el error 500:")
        print("   1. Verificar tamaño del video subido")
        print("   2. Comprobar formato del video")
        print("   3. Revisar logs específicos de error")
        print("   4. Verificar permisos del directorio media")
        
        print("\n📋 Comandos útiles:")
        print("   docker-compose logs -f web | grep -i 'video\\|media\\|upload'")
        print("   docker-compose exec web ls -la /app/media/")
        print("   docker-compose exec web python manage.py check")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()