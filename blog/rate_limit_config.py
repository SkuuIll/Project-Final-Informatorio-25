"""
Configuración avanzada para rate limiting.
"""
from django.conf import settings

# Configuración de rate limits por defecto
DEFAULT_RATE_LIMITS = {
    # Rate limits globales
    'global': {
        'anonymous': '500/h',
        'authenticated': '2000/h',
        'staff': '5000/h',
    },
    
    # Rate limits para API
    'api': {
        'anonymous': '100/h',
        'authenticated': '1000/h',
        'staff': '2000/h',
    },
    
    # Rate limits para búsquedas
    'search': {
        'anonymous': '20/m',
        'authenticated': '50/m',
        'staff': '100/m',
    },
    
    # Rate limits para acciones de usuario
    'user_actions': {
        'likes': '30/m',
        'comments': '20/m',
        'posts': '10/h',
        'follows': '50/h',
    },
    
    # Rate limits para autenticación
    'auth': {
        'login': '10/m',
        'register': '5/m',
        'password_reset': '3/m',
    },
    
    # Rate limits para subidas
    'upload': {
        'images': '20/m',
        'files': '10/m',
        'total_size': '100MB/h',  # Límite por tamaño total
    },
    
    # Rate limits para administración
    'admin': {
        'actions': '200/m',
        'bulk_operations': '10/m',
    },
    
    # Rate limits especiales
    'special': {
        'suspicious': '5/m',
        'bot_legitimate': '60/m',
        'bot_suspicious': '10/m',
        'ddos_threshold': '100/m',
    }
}

# Configuración de IPs en whitelist
WHITELIST_IPS = getattr(settings, 'RATE_LIMIT_WHITELIST_IPS', [
    '127.0.0.1',
    '::1',
])

# Configuración de User-Agents permitidos
ALLOWED_USER_AGENTS = getattr(settings, 'ALLOWED_USER_AGENTS', [
    'googlebot',
    'bingbot',
    'slurp',
    'duckduckbot',
    'baiduspider',
    'yandexbot',
    'facebookexternalhit',
    'twitterbot',
    'linkedinbot',
])

# Configuración de User-Agents sospechosos
SUSPICIOUS_USER_AGENTS = getattr(settings, 'SUSPICIOUS_USER_AGENTS', [
    'bot',
    'crawler',
    'spider',
    'scraper',
    'curl',
    'wget',
    'python-requests',
    'python-urllib',
    'scrapy',
    'mechanize',
    'selenium',
])

# Rutas que requieren rate limiting especial
API_PATHS = getattr(settings, 'RATE_LIMIT_API_PATHS', [
    '/api/',
    '/ajax/',
    '/json/',
])

AUTH_PATHS = getattr(settings, 'RATE_LIMIT_AUTH_PATHS', [
    '/login/',
    '/register/',
    '/password/',
    '/accounts/login/',
    '/accounts/register/',
])

UPLOAD_PATHS = getattr(settings, 'RATE_LIMIT_UPLOAD_PATHS', [
    '/upload/',
    '/media/',
    '/ckeditor/',
])

ADMIN_PATHS = getattr(settings, 'RATE_LIMIT_ADMIN_PATHS', [
    '/admin/',
    '/staff/',
])


def get_rate_limit_for_user(user, category, action=None):
    """
    Obtiene el rate limit apropiado para un usuario específico.
    
    Args:
        user: Usuario de Django (puede ser AnonymousUser)
        category: Categoría de rate limit (ej: 'api', 'search')
        action: Acción específica (opcional)
    
    Returns:
        str: Rate limit en formato "número/período"
    """
    # Obtener configuración personalizada desde settings
    custom_limits = getattr(settings, 'CUSTOM_RATE_LIMITS', {})
    
    # Determinar el tipo de usuario
    if not user.is_authenticated:
        user_type = 'anonymous'
    elif user.is_staff:
        user_type = 'staff'
    else:
        user_type = 'authenticated'
    
    # Buscar en configuración personalizada primero
    if category in custom_limits:
        if action and action in custom_limits[category]:
            if user_type in custom_limits[category][action]:
                return custom_limits[category][action][user_type]
        elif user_type in custom_limits[category]:
            return custom_limits[category][user_type]
    
    # Buscar en configuración por defecto
    if category in DEFAULT_RATE_LIMITS:
        if action and action in DEFAULT_RATE_LIMITS[category]:
            if isinstance(DEFAULT_RATE_LIMITS[category][action], dict):
                return DEFAULT_RATE_LIMITS[category][action].get(user_type, '100/h')
            else:
                return DEFAULT_RATE_LIMITS[category][action]
        elif user_type in DEFAULT_RATE_LIMITS[category]:
            return DEFAULT_RATE_LIMITS[category][user_type]
    
    # Valor por defecto
    return '100/h'


def get_cache_key_for_user(user, group, additional_info=None):
    """
    Genera una clave de caché única para rate limiting.
    
    Args:
        user: Usuario de Django
        group: Grupo de rate limiting
        additional_info: Información adicional para la clave
    
    Returns:
        str: Clave de caché
    """
    if user.is_authenticated:
        identifier = f"user:{user.id}"
    else:
        # Para usuarios anónimos, necesitamos la IP (debe pasarse como additional_info)
        identifier = f"ip:{additional_info}" if additional_info else "anonymous"
    
    return f"ratelimit:{group}:{identifier}"


def is_ip_whitelisted(ip):
    """
    Verifica si una IP está en la whitelist.
    
    Args:
        ip: Dirección IP
    
    Returns:
        bool: True si está en whitelist
    """
    return ip in WHITELIST_IPS


def is_user_agent_allowed(user_agent):
    """
    Verifica si un User-Agent está permitido.
    
    Args:
        user_agent: String del User-Agent
    
    Returns:
        tuple: (is_allowed, is_suspicious)
    """
    user_agent_lower = user_agent.lower()
    
    # Verificar si es un bot permitido
    is_allowed_bot = any(bot in user_agent_lower for bot in ALLOWED_USER_AGENTS)
    
    # Verificar si es sospechoso
    is_suspicious = any(pattern in user_agent_lower for pattern in SUSPICIOUS_USER_AGENTS)
    
    return is_allowed_bot, is_suspicious


def get_progressive_rate_limit(violations, base_rate='100/m', max_reduction=4):
    """
    Calcula un rate limit progresivo basado en violaciones previas.
    
    Args:
        violations: Número de violaciones previas
        base_rate: Rate limit base
        max_reduction: Máxima reducción (factor)
    
    Returns:
        str: Rate limit ajustado
    """
    try:
        count, period = base_rate.split('/')
        count = int(count)
        
        # Reducir el límite basado en violaciones
        reduction_factor = min(2 ** violations, max_reduction)
        adjusted_count = max(1, count // reduction_factor)
        
        return f"{adjusted_count}/{period}"
    except (ValueError, ZeroDivisionError):
        return base_rate


class RateLimitConfig:
    """
    Clase para manejar la configuración de rate limiting.
    """
    
    def __init__(self):
        self.limits = DEFAULT_RATE_LIMITS.copy()
        self.whitelist_ips = WHITELIST_IPS.copy()
        self.allowed_user_agents = ALLOWED_USER_AGENTS.copy()
        self.suspicious_user_agents = SUSPICIOUS_USER_AGENTS.copy()
    
    def update_limits(self, new_limits):
        """Actualiza los límites de rate limiting."""
        self.limits.update(new_limits)
    
    def add_whitelist_ip(self, ip):
        """Agrega una IP a la whitelist."""
        if ip not in self.whitelist_ips:
            self.whitelist_ips.append(ip)
    
    def remove_whitelist_ip(self, ip):
        """Remueve una IP de la whitelist."""
        if ip in self.whitelist_ips:
            self.whitelist_ips.remove(ip)
    
    def get_limit(self, category, user_type='anonymous', action=None):
        """Obtiene un límite específico."""
        if category in self.limits:
            if action and action in self.limits[category]:
                if isinstance(self.limits[category][action], dict):
                    return self.limits[category][action].get(user_type, '100/h')
                else:
                    return self.limits[category][action]
            elif user_type in self.limits[category]:
                return self.limits[category][user_type]
        return '100/h'


# Instancia global de configuración
rate_limit_config = RateLimitConfig()