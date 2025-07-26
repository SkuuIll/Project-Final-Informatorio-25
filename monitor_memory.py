#!/usr/bin/env python3
"""
Script de monitoreo de memoria para el servidor Django.
Útil para diagnosticar problemas de memoria durante la generación de IA.
"""

import psutil
import time
import logging
import os
import sys
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/memory_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class MemoryMonitor:
    def __init__(self, threshold_percent=80, check_interval=30):
        self.threshold_percent = threshold_percent
        self.check_interval = check_interval
        self.process = psutil.Process()
        
    def get_memory_info(self):
        """Obtiene información detallada de memoria."""
        # Memoria del sistema
        system_memory = psutil.virtual_memory()
        
        # Memoria del proceso actual
        process_memory = self.process.memory_info()
        
        # Memoria de todos los procesos Python/Gunicorn
        python_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
            try:
                if proc.info['name'] in ['python', 'python3', 'gunicorn']:
                    python_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cmdline': ' '.join(proc.info['cmdline'][:3]) if proc.info['cmdline'] else ''
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
                
        return {
            'system': {
                'total_gb': system_memory.total / 1024 / 1024 / 1024,
                'available_gb': system_memory.available / 1024 / 1024 / 1024,
                'used_percent': system_memory.percent,
                'free_gb': system_memory.free / 1024 / 1024 / 1024
            },
            'current_process': {
                'rss_mb': process_memory.rss / 1024 / 1024,
                'vms_mb': process_memory.vms / 1024 / 1024,
                'pid': self.process.pid
            },
            'python_processes': python_processes
        }
    
    def log_memory_status(self):
        """Registra el estado actual de la memoria."""
        memory_info = self.get_memory_info()
        
        logger.info("=== ESTADO DE MEMORIA ===")
        logger.info(f"Sistema - Total: {memory_info['system']['total_gb']:.1f}GB, "
                   f"Usado: {memory_info['system']['used_percent']:.1f}%, "
                   f"Disponible: {memory_info['system']['available_gb']:.1f}GB")
        
        logger.info(f"Proceso actual (PID {memory_info['current_process']['pid']}) - "
                   f"RSS: {memory_info['current_process']['rss_mb']:.1f}MB, "
                   f"VMS: {memory_info['current_process']['vms_mb']:.1f}MB")
        
        logger.info("Procesos Python activos:")
        for proc in memory_info['python_processes']:
            logger.info(f"  PID {proc['pid']}: {proc['name']} - {proc['memory_mb']:.1f}MB - {proc['cmdline']}")
        
        # Alerta si el uso de memoria es alto
        if memory_info['system']['used_percent'] > self.threshold_percent:
            logger.warning(f"⚠️  ALERTA: Uso de memoria alto ({memory_info['system']['used_percent']:.1f}%)")
            
        return memory_info
    
    def cleanup_memory(self):
        """Intenta liberar memoria."""
        import gc
        logger.info("Ejecutando limpieza de memoria...")
        
        # Forzar garbage collection
        collected = gc.collect()
        logger.info(f"Garbage collector liberó {collected} objetos")
        
        # Limpiar caché de Django si está disponible
        try:
            from django.core.cache import cache
            cache.clear()
            logger.info("Caché de Django limpiado")
        except ImportError:
            logger.info("Django no disponible para limpiar caché")
    
    def monitor_continuous(self):
        """Monitoreo continuo de memoria."""
        logger.info(f"Iniciando monitoreo continuo de memoria (intervalo: {self.check_interval}s)")
        
        try:
            while True:
                memory_info = self.log_memory_status()
                
                # Si el uso de memoria es muy alto, intentar limpiar
                if memory_info['system']['used_percent'] > self.threshold_percent:
                    self.cleanup_memory()
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoreo detenido por el usuario")
        except Exception as e:
            logger.error(f"Error en monitoreo: {e}")

def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor de memoria para Django')
    parser.add_argument('--threshold', type=int, default=80, 
                       help='Umbral de memoria para alertas (porcentaje)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Intervalo de monitoreo en segundos')
    parser.add_argument('--once', action='store_true',
                       help='Ejecutar una sola vez en lugar de monitoreo continuo')
    
    args = parser.parse_args()
    
    monitor = MemoryMonitor(
        threshold_percent=args.threshold,
        check_interval=args.interval
    )
    
    if args.once:
        monitor.log_memory_status()
    else:
        monitor.monitor_continuous()

if __name__ == '__main__':
    main()