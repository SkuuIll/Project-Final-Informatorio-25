#!/usr/bin/env python3
"""
Script para solucionar problemas comunes de Docker.
"""

import subprocess
import sys
import time

def run_command(command, description, ignore_errors=False):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n🔧 {description}")
    print("-" * 40)
    try:
        result = subprocess.run(command, shell=True, text=True)
        if result.returncode == 0:
            print("✅ Completado exitosamente")
            return True
        elif ignore_errors:
            print("⚠️  Completado con advertencias")
            return True
        else:
            print("❌ Error en la ejecución")
            return False
    except Exception as e:
        print(f"❌ Error ejecutando comando: {e}")
        return False

def stop_all_containers():
    """Detiene todos los contenedores."""
    print("🛑 Deteniendo todos los contenedores...")
    run_command("docker-compose down", "Deteniendo servicios", ignore_errors=True)
    run_command("docker stop $(docker ps -aq)", "Deteniendo contenedores restantes", ignore_errors=True)

def clean_docker_system():
    """Limpia el sistema Docker."""
    print("🧹 Limpiando sistema Docker...")
    
    commands = [
        ("docker system prune -f", "Limpiando sistema Docker"),
        ("docker volume prune -f", "Limpiando volúmenes no utilizados"),
        ("docker network prune -f", "Limpiando redes no utilizadas"),
        ("docker image prune -f", "Limpiando imágenes no utilizadas"),
    ]
    
    for command, description in commands:
        run_command(command, description, ignore_errors=True)

def remove_problematic_volumes():
    """Remueve volúmenes problemáticos."""
    print("📦 Removiendo volúmenes problemáticos...")
    
    volumes = [
        "project_postgres_data",
        "project_redis_data",
        "project_media_files",
        "project_static_files"
    ]
    
    for volume in volumes:
        run_command(f"docker volume rm {volume}", f"Removiendo volumen {volume}", ignore_errors=True)

def check_disk_space():
    """Verifica espacio en disco."""
    print("💾 Verificando espacio en disco...")
    run_command("df -h", "Espacio en disco")
    run_command("docker system df", "Uso de espacio Docker")

def fix_permissions():
    """Arregla permisos de archivos."""
    print("🔐 Arreglando permisos...")
    commands = [
        ("chmod +x init-db.sh", "Permisos de script de DB"),
        ("chmod +x manage_environment.py", "Permisos de gestión de entorno"),
        ("chmod +x deploy_server.py", "Permisos de despliegue"),
        ("chmod +x debug_docker.py", "Permisos de debug"),
    ]
    
    for command, description in commands:
        run_command(command, description, ignore_errors=True)

def rebuild_containers():
    """Reconstruye los contenedores."""
    print("🔨 Reconstruyendo contenedores...")
    
    # Usar docker-compose.server.yml si existe
    compose_file = "docker-compose.server.yml"
    
    commands = [
        (f"docker-compose -f {compose_file} build --no-cache", "Construyendo imágenes sin caché"),
        (f"docker-compose -f {compose_file} up -d", "Iniciando servicios"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"❌ Falló: {description}")
            return False
    
    return True

def wait_for_services():
    """Espera a que los servicios estén listos."""
    print("⏳ Esperando a que los servicios estén listos...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        result = subprocess.run("docker-compose ps", shell=True, capture_output=True, text=True)
        if "healthy" in result.stdout or "Up" in result.stdout:
            print("✅ Servicios están funcionando")
            return True
        
        print(f"Intento {attempt + 1}/{max_attempts} - Esperando...")
        time.sleep(10)
    
    print("❌ Los servicios no se iniciaron correctamente")
    return False

def show_logs():
    """Muestra logs de los servicios."""
    print("📋 Mostrando logs de servicios...")
    run_command("docker-compose logs --tail=50", "Logs recientes", ignore_errors=True)

def main():
    """Función principal."""
    print("🚨 DevBlog - Reparación de Docker")
    print("=" * 50)
    
    # Verificar espacio en disco
    check_disk_space()
    
    # Detener todos los contenedores
    stop_all_containers()
    
    # Limpiar sistema Docker
    clean_docker_system()
    
    # Remover volúmenes problemáticos
    remove_problematic_volumes()
    
    # Arreglar permisos
    fix_permissions()
    
    # Reconstruir contenedores
    if rebuild_containers():
        # Esperar a que los servicios estén listos
        if wait_for_services():
            print("\n🎉 ¡Reparación completada exitosamente!")
            print("🌐 Verifica tu sitio en: http://proyecto.skulll.site")
        else:
            print("\n⚠️  Los servicios se iniciaron pero pueden tener problemas")
            show_logs()
    else:
        print("\n❌ La reparación falló")
        show_logs()
    
    print("\n📝 Comandos útiles:")
    print("docker-compose logs -f web    # Ver logs del servidor web")
    print("docker-compose logs -f db     # Ver logs de la base de datos")
    print("docker-compose ps             # Ver estado de servicios")

if __name__ == "__main__":
    main()