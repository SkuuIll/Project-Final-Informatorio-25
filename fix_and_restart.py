#!/usr/bin/env python3
"""
Script para verificar que los imports están corregidos y reiniciar el servicio.
"""

import os
import subprocess
import time

def check_imports():
    """Verificar que los imports están corregidos."""
    print("🔍 Verificando imports corregidos...\n")
    
    # Verificar que no hay imports problemáticos
    problematic_patterns = [
        "from .services import",
        "from .prompt_manager import", 
        "from .forms import",
        "from .ai_generator import"
    ]
    
    file_path = "posts/views/main.py"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        problems_found = []
        
        for pattern in problematic_patterns:
            if pattern in content:
                problems_found.append(pattern)
        
        if problems_found:
            print("❌ Aún hay imports problemáticos:")
            for problem in problems_found:
                print(f"   • {problem}")
            return False
        else:
            print("✅ Todos los imports están corregidos")
            return True
            
    except Exception as e:
        print(f"❌ Error verificando imports: {e}")
        return False

def restart_web_service():
    """Reiniciar el servicio web."""
    print("\n🔄 Reiniciando servicio web...\n")
    
    try:
        # Reiniciar el servicio web
        print("🛑 Deteniendo servicio web...")
        result = subprocess.run(['docker-compose', 'restart', 'web'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Servicio web reiniciado exitosamente")
            return True
        else:
            print(f"❌ Error reiniciando servicio: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout reiniciando servicio")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def wait_for_service():
    """Esperar a que el servicio esté listo."""
    print("\n⏳ Esperando a que el servicio esté listo...\n")
    
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        try:
            # Verificar logs para ver si hay errores
            result = subprocess.run(['docker-compose', 'logs', '--tail=10', 'web'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logs = result.stdout
                
                # Buscar indicadores de que el servicio está funcionando
                if "Booting worker" in logs or "Application startup complete" in logs or "Listening at" in logs:
                    print("✅ Servicio web está funcionando")
                    return True
                
                # Buscar errores
                if "ModuleNotFoundError" in logs or "ImportError" in logs:
                    print("❌ Aún hay errores de import en los logs")
                    print("📋 Últimos logs:")
                    print(logs[-500:])  # Últimos 500 caracteres
                    return False
            
            attempt += 1
            print(f"⏳ Intento {attempt}/{max_attempts}...")
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error verificando servicio: {e}")
            attempt += 1
            time.sleep(2)
    
    print("⏰ Timeout esperando el servicio")
    return False

def test_site():
    """Probar que el sitio funciona."""
    print("\n🧪 Probando que el sitio funciona...\n")
    
    try:
        # Intentar hacer una petición HTTP simple
        import urllib.request
        import urllib.error
        
        try:
            response = urllib.request.urlopen('http://localhost:8000/', timeout=10)
            status_code = response.getcode()
            
            if status_code == 200:
                print("✅ ¡Sitio web funciona correctamente!")
                return True
            else:
                print(f"⚠️ Sitio responde con código {status_code}")
                return False
                
        except urllib.error.HTTPError as e:
            print(f"❌ Error HTTP: {e.code}")
            return False
        except urllib.error.URLError as e:
            print(f"❌ Error de conexión: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error probando sitio: {e}")
        return False

def main():
    """Función principal."""
    print("🔧 CORRECCIÓN Y REINICIO DEL SERVICIO WEB\n")
    
    # 1. Verificar imports
    if not check_imports():
        print("❌ Los imports no están corregidos correctamente")
        return
    
    # 2. Reiniciar servicio
    if not restart_web_service():
        print("❌ No se pudo reiniciar el servicio")
        return
    
    # 3. Esperar a que esté listo
    if not wait_for_service():
        print("❌ El servicio no se inició correctamente")
        print("\n💡 Comandos para debugging:")
        print("   docker-compose logs -f web")
        print("   docker-compose ps")
        return
    
    # 4. Probar el sitio
    if test_site():
        print("\n🎉 ¡PROBLEMA RESUELTO!")
        print("   El sitio web está funcionando correctamente")
        print("   Ya puedes acceder normalmente")
    else:
        print("\n⚠️ El servicio se reinició pero el sitio aún no responde")
        print("   Puede necesitar unos minutos más para estar completamente listo")
    
    print("\n📋 Resumen de la corrección:")
    print("   🔧 Problema: Imports incorrectos después de mover vistas")
    print("   ✅ Solución: Corregidos imports relativos (. → ..)")
    print("   🔄 Acción: Servicio web reiniciado")
    
    print("\n💡 Si el problema persiste:")
    print("   docker-compose down && docker-compose up -d")

if __name__ == "__main__":
    main()