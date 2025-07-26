#!/usr/bin/env python3
"""
Script para verificar y configurar AppArmor.
"""

import subprocess
import os

def check_apparmor_status():
    """Verificar estado de AppArmor."""
    print("🛡️ Verificando AppArmor...")
    
    try:
        result = subprocess.run(['aa-status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AppArmor está activo")
            print("📋 Estado:")
            print(result.stdout)
            
            # Buscar perfiles relacionados con web
            lines = result.stdout.split('\n')
            web_profiles = []
            for line in lines:
                if any(web_app in line.lower() for web_app in ['nginx', 'apache', 'python', 'django']):
                    web_profiles.append(line.strip())
            
            if web_profiles:
                print("🌐 Perfiles web encontrados:")
                for profile in web_profiles:
                    print(f"   • {profile}")
            
            return True
        else:
            print("❌ Error ejecutando aa-status")
            return False
    except FileNotFoundError:
        print("✅ AppArmor no está instalado")
        return False
    except Exception as e:
        print(f"❌ Error verificando AppArmor: {e}")
        return False

def suggest_apparmor_fixes():
    """Sugerir correcciones para AppArmor."""
    print("\n🔧 Sugerencias para AppArmor:")
    
    media_path = "/home/project/project/media"
    
    print("1. Poner perfiles en modo complain (menos restrictivo):")
    print("   sudo aa-complain /usr/sbin/nginx")
    print("   sudo aa-complain /usr/bin/python3*")
    
    print("\n2. O agregar reglas específicas al perfil:")
    print(f"   # Agregar a /etc/apparmor.d/usr.sbin.nginx:")
    print(f"   {media_path}/** rw,")
    print(f"   {media_path}/ rw,")
    
    print("\n3. Recargar perfiles después de cambios:")
    print("   sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx")
    
    print("\n4. Verificar logs de AppArmor:")
    print("   sudo dmesg | grep -i apparmor")
    print("   sudo journalctl -f | grep -i apparmor")

def main():
    """Función principal."""
    print("🛡️ Verificación de AppArmor para Django\n")
    
    apparmor_active = check_apparmor_status()
    
    if apparmor_active:
        suggest_apparmor_fixes()
        
        print("\n⚠️ IMPORTANTE:")
        print("AppArmor puede bloquear la eliminación de archivos.")
        print("Si la eliminación no funciona después de configurar permisos,")
        print("ejecuta los comandos sugeridos arriba.")
    
    print("\n🧪 Para probar eliminación:")
    print("1. Aplicar permisos: sudo chown -R www-data:www-data /home/project/project/media")
    print("2. Configurar AppArmor si es necesario")
    print("3. Reiniciar servidor web")
    print("4. Probar desde la galería web")

if __name__ == "__main__":
    main()