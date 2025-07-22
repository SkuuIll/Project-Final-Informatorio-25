# Sistema de Rate Limiting

Este documento describe el sistema avanzado de rate limiting implementado en el proyecto DevBlog para proteger las APIs y prevenir abusos.

## Características Principales

- **Rate limiting por usuario y por IP**
- **Diferentes límites según el tipo de usuario** (anónimo, autenticado, staff)
- **Protección contra ataques DDoS**
- **Detección de bots maliciosos**
- **Rate limiting progresivo** (se vuelve más estricto con violaciones repetidas)
- **Whitelist de IPs confiables**
- **Monitoreo y estadísticas en tiempo real**

## Configuración

### Variables de Entorno

```bash
# Rate limits globales
GLOBAL_RATE_LIMIT=1000/h
API_RATE_LIMIT=200/h
SUSPICIOUS_RATE_LIMIT=10/m

# Protección DDoS
DDOS_THRESHOLD=100/m
DDOS_BLOCK_DURATION=3600
```

### Configuración en Settings

```python
# Configuración avanzada de Rate Limiting
GLOBAL_RATE_LIMIT = '1000/h'
API_RATE_LIMIT = '200/h'
SUSPICIOUS_RATE_LIMIT = '10/m'

# Rutas especiales
API_PATHS = ['/api/', '/ajax/', '/json/']
AUTH_PATHS = ['/login/', '/register/', '/password/']
UPLOAD_PATHS = ['/upload/', '/media/', '/ckeditor/']

# IPs en whitelist
RATE_LIMIT_WHITELIST_IPS = ['127.0.0.1', '::1']

# User-Agents permitidos
ALLOWED_USER_AGENTS = ['googlebot', 'bingbot', 'slurp']

# User-Agents sospechosos
SUSPICIOUS_USER_AGENTS = ['bot', 'crawler', 'scraper']
```

## Uso de Decoradores

### Decorador Básico de API

```python
from blog.decorators import api_rate_limit

@api_rate_limit(group='posts', rate='100/m')
def my_api_view(request):
    # Tu código aquí
    pass
```

### Decorador de Búsqueda

```python
from blog.decorators import search_rate_limit

@search_rate_limit(rate='30/m')
def search_view(request):
    # Tu código aquí
    pass
```

### Decorador de Acciones de Usuario

```python
from blog.decorators import user_action_limit

@user_action_limit(group='likes', rate='30/m')
def like_post(request):
    # Tu código aquí
    pass
```

### Decorador de Subidas

```python
from blog.decorators import upload_rate_limit

@upload_rate_limit(rate='20/m')
def upload_image(request):
    # Tu código aquí
    pass
```

### Decorador de Autenticación

```python
from blog.decorators import auth_rate_limit

@auth_rate_limit(rate='10/m')
def login_view(request):
    # Tu código aquí
    pass
```

### Decorador Progresivo

```python
from blog.decorators import progressive_rate_limit

@progressive_rate_limit(base_rate='100/m', escalation_factor=2)
def sensitive_api(request):
    # Tu código aquí
    pass
```

### Decorador con Whitelist

```python
from blog.decorators import ip_whitelist_rate_limit

@ip_whitelist_rate_limit(
    whitelist_ips=['192.168.1.100'],
    rate='1000/m',
    fallback_rate='100/m'
)
def admin_api(request):
    # Tu código aquí
    pass
```

## Middleware

El sistema incluye tres middlewares principales:

### 1. AdvancedRateLimitMiddleware

Aplica rate limiting automático basado en rutas:

- **APIs**: Límites específicos para endpoints de API
- **Autenticación**: Límites estrictos para login/registro
- **Subidas**: Límites para archivos y media
- **Global**: Límite general para todas las solicitudes

### 2. DDoSProtectionMiddleware

Protección contra ataques de denegación de servicio:

- Detecta patrones de tráfico anómalos
- Bloquea IPs temporalmente
- Registra intentos de ataque

### 3. BotDetectionMiddleware

Detecta y maneja bots:

- **Bots legítimos**: Rate limiting suave
- **Bots sospechosos**: Rate limiting estricto
- **Bots maliciosos**: Bloqueo automático

## Comandos de Gestión

### Ver Estado

```bash
python manage.py manage_rate_limits --action status
```

### Limpiar Rate Limits

```bash
# Limpiar todos
python manage.py manage_rate_limits --action clear

# Limpiar por IP
python manage.py manage_rate_limits --action clear --ip 192.168.1.100

# Limpiar por usuario
python manage.py manage_rate_limits --action clear --user-id 123

# Limpiar por grupo
python manage.py manage_rate_limits --action clear --group api
```

### Gestionar Whitelist

```bash
# Agregar/remover IP de whitelist
python manage.py manage_rate_limits --action whitelist --ip 192.168.1.100
```

### Blacklist Temporal

```bash
# Bloquear IP temporalmente
python manage.py manage_rate_limits --action blacklist --ip 192.168.1.100 --duration 3600
```

### Ver Estadísticas

```bash
# Ver estadísticas
python manage.py manage_rate_limits --action stats

# Exportar estadísticas
python manage.py manage_rate_limits --action stats --export stats.json
```

## Configuración Personalizada

### Rate Limits por Tipo de Usuario

```python
CUSTOM_RATE_LIMITS = {
    'api': {
        'anonymous': '50/h',
        'authenticated': '500/h',
        'staff': '2000/h',
    },
    'search': {
        'anonymous': '10/m',
        'authenticated': '30/m',
        'staff': '100/m',
    },
    'user_actions': {
        'likes': '20/m',
        'comments': '10/m',
        'posts': '5/h',
    }
}
```

### Configuración Dinámica

```python
from blog.rate_limit_config import rate_limit_config

# Actualizar límites en tiempo de ejecución
rate_limit_config.update_limits({
    'special_api': {
        'authenticated': '1000/h'
    }
})

# Agregar IP a whitelist
rate_limit_config.add_whitelist_ip('192.168.1.200')
```

## Monitoreo y Alertas

### Headers de Respuesta

El sistema agrega headers informativos a las respuestas:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Logging

Todos los eventos de rate limiting se registran:

```python
import logging
logger = logging.getLogger('django.security')

# Los logs incluyen:
# - IP del cliente
# - ID de usuario (si está autenticado)
# - Ruta solicitada
# - Tipo de violación
# - Límites aplicados
```

### Métricas

El sistema puede integrarse con Prometheus para métricas:

```python
from django_prometheus.models import ExportModelOperationsMixin

# Métricas disponibles:
# - rate_limit_violations_total
# - rate_limit_requests_total
# - ddos_attacks_blocked_total
# - suspicious_requests_total
```

## Mejores Prácticas

1. **Configurar límites apropiados**: No demasiado restrictivos para usuarios legítimos
2. **Usar whitelist para IPs confiables**: Servidores internos, CDNs, etc.
3. **Monitorear regularmente**: Revisar logs y estadísticas
4. **Ajustar según el tráfico**: Adaptar límites al crecimiento
5. **Implementar alertas**: Notificar sobre ataques o anomalías
6. **Documentar excepciones**: Mantener registro de IPs whitelistadas

## Solución de Problemas

### Rate Limit Falso Positivo

```bash
# Verificar límites actuales
python manage.py manage_rate_limits --action status --ip 192.168.1.100

# Limpiar límites si es necesario
python manage.py manage_rate_limits --action clear --ip 192.168.1.100

# Agregar a whitelist si es confiable
python manage.py manage_rate_limits --action whitelist --ip 192.168.1.100
```

### Bot Legítimo Bloqueado

1. Verificar User-Agent en logs
2. Agregar a `ALLOWED_USER_AGENTS` si es legítimo
3. Reiniciar aplicación para aplicar cambios

### Ataque DDoS

1. Verificar logs de seguridad
2. Identificar IPs atacantes
3. Agregar a blacklist temporal o permanente
4. Ajustar `DDOS_THRESHOLD` si es necesario

## Integración con CDN

Para usar con CloudFlare u otros CDNs:

```python
# Configurar headers de IP real
AXES_META_PRECEDENCE_ORDER = [
    'HTTP_CF_CONNECTING_IP',  # CloudFlare
    'HTTP_X_FORWARDED_FOR',
    'REMOTE_ADDR',
]

# Whitelist IPs de CDN
RATE_LIMIT_WHITELIST_IPS = [
    # IPs de CloudFlare
    '103.21.244.0/22',
    '103.22.200.0/22',
    # ... más rangos
]
```