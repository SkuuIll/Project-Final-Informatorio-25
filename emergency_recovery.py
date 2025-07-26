#!/usr/bin/env python3
"""
Script de recuperación de emergencia para error 500.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')
django.setup()

from posts.models import Post
from django.contrib.auth.models import User

def find_problematic_post():
    """Encontrar el post que puede estar causando el problema."""
    print("🔍 Buscando post problemático...\n")
    
    try:
        # Buscar posts recientes (últimas 2 horas)
        recent_time = datetime.now() - timedelta(hours=2)
        recent_posts = Post.objects.filter(created_at__gte=recent_time).order_by('-created_at')
        
        print(f"📋 Posts recientes (últimas 2 horas): {recent_posts.count()}")
        
        for post in recent_posts:
            print(f"\n📄 Post ID: {post.id}")
            print(f"   Título: {post.title}")
            print(f"   Autor: {post.author}")
            print(f"   Fecha: {post.created_at}")
            print(f"   Estado: {post.status}")
            
            # Verificar contenido problemático
            if post.content:
                content_length = len(post.content)
                print(f"   Tamaño contenido: {content_length} caracteres")
                
                # Buscar elementos de video
                video_indicators = ['<video', 'youtube', 'vimeo', 'embed', 'iframe', 'media']
                found_video = []
                
                for indicator in video_indicators:
                    if indicator in post.content.lower():
                        found_video.append(indicator)
                
                if found_video:
                    print(f"   🎥 Contiene video: {', '.join(found_video)}")
                    print(f"   ⚠️ POSIBLE CAUSA DEL ERROR")
                    
                    # Mostrar fragmento del contenido con video
                    content_lower = post.content.lower()
                    for indicator in found_video:
                        index = content_lower.find(indicator)
                        if index != -1:
                            start = max(0, index - 50)
                            end = min(len(post.content), index + 200)
                            fragment = post.content[start:end]
                            print(f"   📝 Fragmento ({indicator}): ...{fragment}...")
                            break
                else:
                    print(f"   📝 Sin elementos de video detectados")
            else:
                print(f"   📝 Sin contenido")
        
        return recent_posts
        
    except Exception as e:
        print(f"❌ Error buscando posts: {e}")
        return []

def backup_problematic_post(post):
    """Hacer backup de un post problemático."""
    print(f"\n💾 Haciendo backup del post ID {post.id}...")
    
    try:
        backup_data = {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': post.author.username,
            'created_at': str(post.created_at),
            'status': post.status
        }
        
        # Guardar backup en archivo
        import json
        backup_filename = f"post_backup_{post.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Backup guardado: {backup_filename}")
        return backup_filename
        
    except Exception as e:
        print(f"❌ Error haciendo backup: {e}")
        return None

def fix_problematic_post(post):
    """Intentar arreglar un post problemático."""
    print(f"\n🔧 Intentando arreglar post ID {post.id}...")
    
    try:
        original_content = post.content
        
        if not original_content:
            print("   ℹ️ Post sin contenido, no hay nada que arreglar")
            return False
        
        # Hacer backup primero
        backup_file = backup_problematic_post(post)
        if not backup_file:
            print("   ❌ No se pudo hacer backup, abortando")
            return False
        
        # Limpiar contenido problemático
        cleaned_content = original_content
        
        # Remover elementos de video problemáticos
        import re
        
        # Patrones problemáticos comunes
        problematic_patterns = [
            r'<video[^>]*>.*?</video>',  # Tags de video
            r'<iframe[^>]*>.*?</iframe>',  # iframes
            r'<embed[^>]*>.*?</embed>',  # embeds
            r'<object[^>]*>.*?</object>',  # objects
        ]
        
        changes_made = False
        
        for pattern in problematic_patterns:
            if re.search(pattern, cleaned_content, re.IGNORECASE | re.DOTALL):
                print(f"   🧹 Removiendo patrón: {pattern[:30]}...")
                cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.IGNORECASE | re.DOTALL)
                changes_made = True
        
        # Limpiar HTML malformado
        if '<' in cleaned_content and '>' in cleaned_content:
            # Remover tags sin cerrar o malformados
            cleaned_content = re.sub(r'<[^>]*$', '', cleaned_content)  # Tags sin cerrar al final
            cleaned_content = re.sub(r'^[^<]*>', '', cleaned_content)  # Tags sin abrir al inicio
        
        if changes_made:
            # Guardar contenido limpio
            post.content = cleaned_content
            post.save()
            
            print(f"   ✅ Post limpiado y guardado")
            print(f"   📊 Tamaño original: {len(original_content)} chars")
            print(f"   📊 Tamaño limpio: {len(cleaned_content)} chars")
            return True
        else:
            print(f"   ℹ️ No se encontraron patrones problemáticos")
            return False
            
    except Exception as e:
        print(f"   ❌ Error arreglando post: {e}")
        return False

def emergency_disable_post(post):
    """Deshabilitar un post como medida de emergencia."""
    print(f"\n🚨 Deshabilitando post ID {post.id} como medida de emergencia...")
    
    try:
        # Hacer backup primero
        backup_file = backup_problematic_post(post)
        
        # Cambiar estado a draft
        post.status = 'draft'
        post.save()
        
        print(f"   ✅ Post cambiado a estado 'draft'")
        print(f"   💾 Backup disponible: {backup_file}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error deshabilitando post: {e}")
        return False

def test_site_recovery():
    """Probar si el sitio se ha recuperado."""
    print(f"\n🧪 Probando recuperación del sitio...")
    
    try:
        # Intentar operaciones básicas de Django
        from django.test import Client
        
        client = Client()
        
        # Probar página principal
        try:
            response = client.get('/')
            print(f"   📄 Página principal: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Página principal funciona")
                return True
            else:
                print(f"   ❌ Página principal devuelve {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error accediendo página principal: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando recuperación: {e}")
        return False

def main():
    """Función principal de recuperación."""
    print("🚨 RECUPERACIÓN DE EMERGENCIA - ERROR 500\n")
    
    try:
        # 1. Encontrar posts problemáticos
        recent_posts = find_problematic_post()
        
        if not recent_posts:
            print("ℹ️ No se encontraron posts recientes problemáticos")
            return
        
        # 2. Intentar arreglar cada post problemático
        fixed_posts = []
        disabled_posts = []
        
        for post in recent_posts:
            if post.content and any(indicator in post.content.lower() 
                                  for indicator in ['<video', 'youtube', 'vimeo', 'embed', 'iframe']):
                
                print(f"\n🎯 Procesando post problemático: {post.title}")
                
                # Intentar arreglar primero
                if fix_problematic_post(post):
                    fixed_posts.append(post)
                    
                    # Probar si el sitio se recuperó
                    if test_site_recovery():
                        print(f"✅ ¡Sitio recuperado después de arreglar post {post.id}!")
                        break
                else:
                    # Si no se puede arreglar, deshabilitar
                    if emergency_disable_post(post):
                        disabled_posts.append(post)
                        
                        # Probar si el sitio se recuperó
                        if test_site_recovery():
                            print(f"✅ ¡Sitio recuperado después de deshabilitar post {post.id}!")
                            break
        
        # 3. Resumen de acciones
        print(f"\n📊 Resumen de recuperación:")
        print(f"   🔧 Posts arreglados: {len(fixed_posts)}")
        print(f"   🚨 Posts deshabilitados: {len(disabled_posts)}")
        
        if fixed_posts:
            print(f"   ✅ Posts arreglados:")
            for post in fixed_posts:
                print(f"     • ID {post.id}: {post.title}")
        
        if disabled_posts:
            print(f"   ⚠️ Posts deshabilitados (revisar manualmente):")
            for post in disabled_posts:
                print(f"     • ID {post.id}: {post.title}")
        
        # 4. Prueba final
        if test_site_recovery():
            print(f"\n🎉 ¡RECUPERACIÓN EXITOSA!")
            print(f"   El sitio debería estar funcionando ahora")
        else:
            print(f"\n❌ El sitio aún no funciona")
            print(f"   Puede requerir intervención manual adicional")
        
        print(f"\n💡 Próximos pasos:")
        print(f"   1. Verificar que el sitio funciona: docker-compose restart web")
        print(f"   2. Revisar posts deshabilitados y arreglarlos manualmente")
        print(f"   3. Restaurar desde backup si es necesario")
        
    except Exception as e:
        print(f"\n❌ Error durante la recuperación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()