"""
Optimizador de memoria para operaciones de IA.
Maneja la liberación de memoria y previene timeouts.
"""

import gc
import time
import logging
from functools import wraps
from typing import Callable, Any, Dict
import psutil
import os

logger = logging.getLogger(__name__)

class AIMemoryManager:
    """Gestor de memoria para operaciones de IA."""
    
    def __init__(self, memory_threshold=0.8, cleanup_interval=30):
        self.memory_threshold = memory_threshold
        self.cleanup_interval = cleanup_interval
        self.last_cleanup = time.time()
    
    def get_memory_usage(self) -> float:
        """Obtiene el uso actual de memoria como porcentaje."""
        try:
            return psutil.virtual_memory().percent / 100
        except:
            return 0.5  # Valor por defecto si no se puede obtener
    
    def cleanup_memory(self) -> bool:
        """Ejecuta limpieza de memoria."""
        try:
            # Forzar garbage collection
            collected = gc.collect()
            
            # Limpiar caché de Django si está disponible
            try:
                from django.core.cache import cache
                cache.clear()
                logger.info(f"Memoria limpiada: {collected} objetos recolectados")
                return True
            except ImportError:
                pass
            
            return collected > 0
        except Exception as e:
            logger.error(f"Error limpiando memoria: {e}")
            return False
    
    def should_cleanup(self) -> bool:
        """Determina si se debe ejecutar limpieza de memoria."""
        current_time = time.time()
        memory_usage = self.get_memory_usage()
        
        # Limpiar si el uso de memoria es alto o ha pasado el intervalo
        return (memory_usage > self.memory_threshold or 
                current_time - self.last_cleanup > self.cleanup_interval)
    
    def monitor_and_cleanup(self):
        """Monitorea y limpia memoria si es necesario."""
        if self.should_cleanup():
            self.cleanup_memory()
            self.last_cleanup = time.time()

# Instancia global del gestor de memoria
memory_manager = AIMemoryManager()

def memory_optimized(func: Callable) -> Callable:
    """
    Decorador que optimiza el uso de memoria para funciones de IA.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Limpieza antes de ejecutar
        memory_manager.monitor_and_cleanup()
        
        try:
            # Ejecutar función
            result = func(*args, **kwargs)
            
            # Limpieza después de ejecutar
            memory_manager.cleanup_memory()
            
            return result
            
        except Exception as e:
            # Limpieza en caso de error
            memory_manager.cleanup_memory()
            raise e
    
    return wrapper

def chunked_processing(items: list, chunk_size: int = 5, delay: float = 0.1):
    """
    Procesa elementos en chunks para evitar sobrecarga de memoria.
    
    Args:
        items: Lista de elementos a procesar
        chunk_size: Tamaño del chunk
        delay: Delay entre chunks en segundos
    """
    for i in range(0, len(items), chunk_size):
        chunk = items[i:i + chunk_size]
        yield chunk
        
        # Pequeño delay y limpieza entre chunks
        if delay > 0:
            time.sleep(delay)
        memory_manager.monitor_and_cleanup()

class ProgressTracker:
    """Tracker de progreso que también monitorea memoria."""
    
    def __init__(self, callback=None):
        self.callback = callback
        self.start_time = time.time()
        self.last_update = time.time()
    
    def update(self, message: str, progress: int):
        """Actualiza progreso y monitorea memoria."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Monitorear memoria cada 10 segundos
        if current_time - self.last_update > 10:
            memory_manager.monitor_and_cleanup()
            self.last_update = current_time
        
        # Callback con información adicional
        if self.callback:
            memory_usage = memory_manager.get_memory_usage()
            enhanced_message = f"{message} (Memoria: {memory_usage:.1%}, Tiempo: {elapsed:.1f}s)"
            self.callback(enhanced_message, progress)
    
    def finish(self):
        """Finaliza el tracking y limpia memoria."""
        memory_manager.cleanup_memory()
        total_time = time.time() - self.start_time
        logger.info(f"Operación completada en {total_time:.1f} segundos")

def timeout_handler(timeout_seconds: int = 240):
    """
    Decorador para manejar timeouts en operaciones de IA.
    
    Args:
        timeout_seconds: Timeout en segundos (default: 4 minutos)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import signal
            
            def timeout_signal_handler(signum, frame):
                raise TimeoutError(f"Operación excedió el timeout de {timeout_seconds} segundos")
            
            # Configurar timeout solo en sistemas Unix
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
                signal.alarm(timeout_seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            except TimeoutError:
                logger.error(f"Timeout en función {func.__name__}")
                raise
            finally:
                # Limpiar timeout
                if hasattr(signal, 'SIGALRM'):
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

# Configuración específica para operaciones de IA
AI_CONFIG = {
    'max_retries': 3,
    'retry_delay': 2,
    'chunk_size': 3,
    'memory_threshold': 0.85,
    'timeout_seconds': 240,  # 4 minutos
}

def get_ai_config(key: str, default=None):
    """Obtiene configuración para operaciones de IA."""
    return AI_CONFIG.get(key, default)