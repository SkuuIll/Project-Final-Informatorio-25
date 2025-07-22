"""
Configuración de rate limiting para la aplicación.
Define reglas y límites para diferentes tipos de solicitudes.
"""

# Reglas de rate limiting por tipo de solicitud
RATELIMIT_RULES = {
    # API general
    'api_default': '200/m',  # 200 solicitudes por minuto
    'api_posts': '100/m',    # 100 solicitudes por minuto para endpoints de posts
    'api_comments': '60/m',  # 60 solicitudes por minuto para endpoints de comentarios
    'api_users': '50/m',     # 50 solicitudes por minuto para endpoints de usuarios
    
    # Acciones de usuario
    'post_likes': '30/m',    # 30 likes por minuto
    'comment_likes': '30/m', # 30 likes de comentarios por minuto
    'post_favorites': '30/m',# 30 favoritos por minuto
    'upload_image': '20/m',  # 20 subidas de imágenes por minuto
    'user_action': '60/m',   # 60 acciones generales por minuto
    
    # Búsquedas
    'search': '30/m',        # 30 búsquedas por minuto
    
    # Autenticación
    'login_attempts': '5/m', # 5 intentos de login por minuto
    'register_attempts': '3/m', # 3 intentos de registro por minuto
    
    # Generación de contenido con IA
    'ai_generation': '5/m',  # 5 generaciones de contenido por minuto
}

# Configuración de rate limiting por tipo de usuario
RATELIMIT_USER_TYPES = {
    'anonymous': {
        'api_default': '50/m',    # Más restrictivo para usuarios anónimos
        'api_posts': '30/m',
        'api_comments': '20/m',
        'search': '10/m',
        'login_attempts': '5/m',
        'register_attempts': '3/m',
    },
    'authenticated': {
        'api_default': '200/m',   # Más permisivo para usuarios autenticados
        'api_posts': '100/m',
        'api_comments': '60/m',
        'search': '30/m',
    },
    'staff': {
        'api_default': '500/m',   # Muy permisivo para staff
        'api_posts': '300/m',
        'api_comments': '200/m',
        'search': '100/m',
    }
}

# Tiempos de espera para diferentes tipos de abuso
RATELIMIT_TIMEOUTS = {
    'default': 60,           # 1 minuto por defecto
    'repeated_abuse': 300,   # 5 minutos para abuso repetido
    'severe_abuse': 3600,    # 1 hora para abuso severo
}

# Configuración para bloqueo progresivo
PROGRESSIVE_RATELIMIT = {
    'enabled': True,
    'base_timeout': 60,      # Tiempo base de bloqueo (segundos)
    'multiplier': 2,         # Multiplicador para cada violación
    'max_timeout': 86400,    # Tiempo máximo de bloqueo (24 horas)
}

def get_rate_limit(group, user=None):
    """
    Obtiene el límite de tasa adecuado según el grupo y el usuario.
    
    Args:
        group: Grupo de rate limiting
        user: Usuario actual (opcional)
    
    Returns:
        Límite de tasa en formato "número/unidad"
    """
    # Determinar tipo de usuario
    user_type = 'anonymous'
    if user and user.is_authenticated:
        user_type = 'staff' if user.is_staff else 'authenticated'
    
    # Buscar límite específico para el tipo de usuario
    if user_type in RATELIMIT_USER_TYPES and group in RATELIMIT_USER_TYPES[user_type]:
        return RATELIMIT_USER_TYPES[user_type][group]
    
    # Usar límite general si existe
    if group in RATELIMIT_RULES:
        return RATELIMIT_RULES[group]
    
    # Valor por defecto
    return RATELIMIT_RULES.get('api_default', '100/m')