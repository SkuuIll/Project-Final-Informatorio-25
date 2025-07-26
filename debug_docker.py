#!/usr/bin/env python3
"""
Script para diagnosticar problemas de Docker en el servidor.
"""

import subprocess
import sys

def run_command(command, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n🔍 {description}")
    print("=" * 50)
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        return False

def main():
    """Función principal de diagnóstico."""
    print("🔧 Diagnóstico de Docker - DevBlog")
    print("=" * 50)
    
    # 1. Ver logs del contenedor de base de datos
    run_command("docker-compose logs db", "Logs del contenedor de base de datos")
    
    # 2. Ver estado de todos los contenedores
    run_command("docker-compose ps", "Estado de contenedores")
    
    # 3. Ver uso de espacio en disco
    run_command("df -h", "Espacio en disco")
    
    # 4. Ver memoria disponible
    run_command("free -h", "Memoria disponible")
    
    # 5. Ver procesos de Docker
    run_command("docker ps -a", "Todos los contenedores Docker")
    
    # 6. Limpiar contenedores y volúmenes
    print("\n🧹 Comandos de limpieza recomendados:")
    print("docker-compose down -v")
    print("docker system prune -f")
    print("docker volume prune -f")
    print("docker-compose up -d --build")

if __name__ == "__main__":
    main()