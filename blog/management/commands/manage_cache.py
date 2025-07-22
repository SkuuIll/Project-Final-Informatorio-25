"""
Comando de gestión para administrar el caché Redis.
"""

from django.core.management.base import BaseCommand
from django.core.cache import cache
from blog.cache_utils import (
    warm_cache_for_posts, 
    warm_cache_for_tags,
    get_cache_stats,
    invalidate_cache_pattern
)


class Command(BaseCommand):
    help = 'Gestiona el caché Redis del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['warm', 'clear', 'stats', 'invalidate'],
            default='stats',
            help='Acción a realizar'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Patrón para invalidar claves específicas'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['posts', 'tags', 'all'],
            default='all',
            help='Tipo de datos para precalentar'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'warm':
            self.warm_cache(options)
        elif action == 'clear':
            self.clear_cache()
        elif action == 'stats':
            self.show_stats()
        elif action == 'invalidate':
            self.invalidate_cache(options)
    
    def warm_cache(self, options):
        """Precalienta el caché con datos frecuentemente accedidos."""
        cache_type = options.get('type', 'all')
        
        self.stdout.write(self.style.SUCCESS('Precalentando caché...'))
        
        if cache_type in ['posts', 'all']:
            warm_cache_for_posts()
            self.stdout.write('✓ Caché de posts precalentado')
        
        if cache_type in ['tags', 'all']:
            warm_cache_for_tags()
            self.stdout.write('✓ Caché de tags precalentado')
        
        self.stdout.write(self.style.SUCCESS('Precalentamiento completado'))
    
    def clear_cache(self):
        """Limpia todo el caché."""
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS('Caché limpiado completamente'))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al limpiar caché: {e}')
            )
    
    def show_stats(self):
        """Muestra estadísticas del caché."""
        self.stdout.write(self.style.SUCCESS('Estadísticas del Caché'))
        self.stdout.write('=' * 50)
        
        stats = get_cache_stats()
        
        if 'error' in stats:
            self.stdout.write(
                self.style.ERROR(f'Error al obtener estadísticas: {stats["error"]}')
            )
            return
        
        for key, value in stats.items():
            if key == 'hit_rate':
                self.stdout.write(f'{key}: {value:.2f}%')
            else:
                self.stdout.write(f'{key}: {value}')
    
    def invalidate_cache(self, options):
        """Invalida claves de caché específicas."""
        pattern = options.get('pattern')
        
        if not pattern:
            self.stdout.write(
                self.style.ERROR('Debe especificar un patrón con --pattern')
            )
            return
        
        try:
            invalidate_cache_pattern(pattern)
            self.stdout.write(
                self.style.SUCCESS(f'Claves con patrón "{pattern}" invalidadas')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al invalidar caché: {e}')
            )