"""
Comando de gestión para monitorear y administrar rate limits.
"""
import json
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth.models import User
from blog.rate_limit_config import rate_limit_config, get_rate_limit_for_user
from blog.ratelimit import get_client_ip


class Command(BaseCommand):
    help = 'Gestiona y monitorea los rate limits del sistema'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['status', 'clear', 'whitelist', 'blacklist', 'stats'],
            default='status',
            help='Acción a realizar'
        )
        parser.add_argument(
            '--ip',
            type=str,
            help='Dirección IP para operaciones específicas'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID de usuario para operaciones específicas'
        )
        parser.add_argument(
            '--group',
            type=str,
            help='Grupo de rate limiting específico'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=3600,
            help='Duración en segundos para blacklist temporal'
        )
        parser.add_argument(
            '--export',
            type=str,
            help='Archivo para exportar estadísticas'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'status':
            self.show_status(options)
        elif action == 'clear':
            self.clear_limits(options)
        elif action == 'whitelist':
            self.manage_whitelist(options)
        elif action == 'blacklist':
            self.manage_blacklist(options)
        elif action == 'stats':
            self.show_stats(options)
    
    def show_status(self, options):
        """Muestra el estado actual de los rate limits."""
        self.stdout.write(self.style.SUCCESS('Estado de Rate Limiting'))
        self.stdout.write('=' * 50)
        
        # Mostrar configuración actual
        self.stdout.write('\nConfiguración actual:')
        for category, limits in rate_limit_config.limits.items():
            self.stdout.write(f"  {category}: {limits}")
        
        # Mostrar IPs en whitelist
        self.stdout.write(f'\nIPs en whitelist: {rate_limit_config.whitelist_ips}')
        
        # Mostrar estadísticas de caché
        self.stdout.write('\nEstadísticas de caché:')
        cache_keys = self._get_rate_limit_cache_keys()
        self.stdout.write(f"  Claves activas: {len(cache_keys)}")
        
        # Mostrar límites activos por IP/usuario
        if options.get('ip') or options.get('user_id'):
            self.show_specific_limits(options)
    
    def clear_limits(self, options):
        """Limpia los rate limits."""
        if options.get('ip'):
            self._clear_ip_limits(options['ip'])
            self.stdout.write(
                self.style.SUCCESS(f"Rate limits limpiados para IP: {options['ip']}")
            )
        elif options.get('user_id'):
            self._clear_user_limits(options['user_id'])
            self.stdout.write(
                self.style.SUCCESS(f"Rate limits limpiados para usuario: {options['user_id']}")
            )
        elif options.get('group'):
            self._clear_group_limits(options['group'])
            self.stdout.write(
                self.style.SUCCESS(f"Rate limits limpiados para grupo: {options['group']}")
            )
        else:
            # Limpiar todos los rate limits
            self._clear_all_limits()
            self.stdout.write(
                self.style.SUCCESS("Todos los rate limits han sido limpiados")
            )
    
    def manage_whitelist(self, options):
        """Gestiona la whitelist de IPs."""
        ip = options.get('ip')
        if not ip:
            self.stdout.write(
                self.style.ERROR("Debe especificar una IP con --ip")
            )
            return
        
        if ip in rate_limit_config.whitelist_ips:
            rate_limit_config.remove_whitelist_ip(ip)
            self.stdout.write(
                self.style.SUCCESS(f"IP {ip} removida de la whitelist")
            )
        else:
            rate_limit_config.add_whitelist_ip(ip)
            self.stdout.write(
                self.style.SUCCESS(f"IP {ip} agregada a la whitelist")
            )
    
    def manage_blacklist(self, options):
        """Gestiona la blacklist temporal de IPs."""
        ip = options.get('ip')
        if not ip:
            self.stdout.write(
                self.style.ERROR("Debe especificar una IP con --ip")
            )
            return
        
        duration = options.get('duration', 3600)
        
        # Agregar a blacklist temporal
        blacklist_key = f"blacklisted:{ip}"
        cache.set(blacklist_key, True, duration)
        
        self.stdout.write(
            self.style.SUCCESS(
                f"IP {ip} agregada a blacklist por {duration} segundos"
            )
        )
    
    def show_stats(self, options):
        """Muestra estadísticas detalladas."""
        self.stdout.write(self.style.SUCCESS('Estadísticas de Rate Limiting'))
        self.stdout.write('=' * 50)
        
        # Obtener todas las claves de rate limiting
        cache_keys = self._get_rate_limit_cache_keys()
        
        # Agrupar por tipo
        stats = {
            'global': [],
            'api': [],
            'search': [],
            'auth': [],
            'upload': [],
            'suspicious': [],
            'other': []
        }
        
        for key in cache_keys:
            data = cache.get(key)
            if data:
                # Determinar categoría
                category = 'other'
                for cat in stats.keys():
                    if cat in key:
                        category = cat
                        break
                
                stats[category].append({
                    'key': key,
                    'count': len(data) if isinstance(data, list) else data,
                    'data': data
                })
        
        # Mostrar estadísticas
        for category, items in stats.items():
            if items:
                self.stdout.write(f'\n{category.upper()}:')
                for item in items[:10]:  # Mostrar solo los primeros 10
                    self.stdout.write(f"  {item['key']}: {item['count']} solicitudes")
        
        # Exportar si se especifica
        if options.get('export'):
            self._export_stats(stats, options['export'])
    
    def show_specific_limits(self, options):
        """Muestra límites específicos para IP o usuario."""
        if options.get('ip'):
            ip = options['ip']
            self.stdout.write(f'\nLímites para IP {ip}:')
            
            # Buscar claves relacionadas con esta IP
            cache_keys = self._get_rate_limit_cache_keys()
            ip_keys = [key for key in cache_keys if ip in key]
            
            for key in ip_keys:
                data = cache.get(key)
                if data:
                    count = len(data) if isinstance(data, list) else data
                    self.stdout.write(f"  {key}: {count}")
        
        if options.get('user_id'):
            user_id = options['user_id']
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f'\nLímites para usuario {user.username} (ID: {user_id}):')
                
                # Mostrar límites configurados
                for category in ['global', 'api', 'search']:
                    limit = get_rate_limit_for_user(user, category)
                    self.stdout.write(f"  {category}: {limit}")
                
                # Buscar claves relacionadas con este usuario
                cache_keys = self._get_rate_limit_cache_keys()
                user_keys = [key for key in cache_keys if f"user:{user_id}" in key]
                
                for key in user_keys:
                    data = cache.get(key)
                    if data:
                        count = len(data) if isinstance(data, list) else data
                        self.stdout.write(f"  {key}: {count}")
                        
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Usuario con ID {user_id} no encontrado")
                )
    
    def _get_rate_limit_cache_keys(self):
        """Obtiene todas las claves de rate limiting del caché."""
        # Nota: Esta implementación depende del backend de caché
        # Para Redis, se puede usar KEYS pattern
        # Para otros backends, puede requerir un enfoque diferente
        
        try:
            # Intentar con Redis
            from django.core.cache.backends.redis import RedisCache
            if isinstance(cache, RedisCache):
                return cache._cache.get_client().keys('ratelimit:*')
        except ImportError:
            pass
        
        # Fallback: retornar lista vacía
        # En producción, se debería implementar un sistema de tracking
        return []
    
    def _clear_ip_limits(self, ip):
        """Limpia los rate limits para una IP específica."""
        cache_keys = self._get_rate_limit_cache_keys()
        ip_keys = [key for key in cache_keys if ip in key.decode() if isinstance(key, bytes) else ip in key]
        
        for key in ip_keys:
            cache.delete(key)
    
    def _clear_user_limits(self, user_id):
        """Limpia los rate limits para un usuario específico."""
        cache_keys = self._get_rate_limit_cache_keys()
        user_keys = [key for key in cache_keys if f"user:{user_id}" in (key.decode() if isinstance(key, bytes) else key)]
        
        for key in user_keys:
            cache.delete(key)
    
    def _clear_group_limits(self, group):
        """Limpia los rate limits para un grupo específico."""
        cache_keys = self._get_rate_limit_cache_keys()
        group_keys = [key for key in cache_keys if group in (key.decode() if isinstance(key, bytes) else key)]
        
        for key in group_keys:
            cache.delete(key)
    
    def _clear_all_limits(self):
        """Limpia todos los rate limits."""
        cache_keys = self._get_rate_limit_cache_keys()
        
        for key in cache_keys:
            cache.delete(key)
    
    def _export_stats(self, stats, filename):
        """Exporta estadísticas a un archivo JSON."""
        try:
            # Convertir datos para serialización JSON
            export_data = {}
            for category, items in stats.items():
                export_data[category] = []
                for item in items:
                    export_data[category].append({
                        'key': item['key'],
                        'count': item['count']
                    })
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.stdout.write(
                self.style.SUCCESS(f"Estadísticas exportadas a {filename}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error al exportar: {e}")
            )