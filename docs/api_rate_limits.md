# API Rate Limiting

Este documento describe la configuración de rate limiting (límites de tasa) implementada para proteger la API del DevBlog contra abusos y ataques.

## Límites de Tasa por Tipo de Endpoint

Los límites de tasa se aplican según el tipo de endpoint y si el usuario está autenticado o no:

| Tipo de Endpoint | Usuarios Autenticados | Usuarios Anónimos | Descripción |
|------------------|----------------------|-------------------|-------------|
| Default          | 100/minuto           | 30/minuto         | Límite general para endpoints no categorizados |
| Search           | 60/minuto            | 20/minuto         | Endpoints de búsqueda |
| Auth             | 20/minuto            | 10/minuto         | Endpoints de autenticación |
| Sensitive        | 30/minuto            | 5/minuto          | Endpoints con información sensible |
| Write            | 50/minuto            | 0/minuto          | Operaciones de escritura (no permitidas para anónimos) |

## Endpoints Protegidos

Los siguientes endpoints tienen protección de rate limiting:

### API REST

- `GET /api/posts/` - Listado de posts (límite default)
- `GET /api/posts/{slug}/` - Detalle de post (límite api_read)
- `POST /api/posts/` - Crear post (límite write)
- `PUT /api/posts/{slug}/` - Actualizar post (límite write)
- `PATCH /api/posts/{slug}/` - Actualizar parcialmente post (límite write)
- `DELETE /api/posts/{slug}/` - Eliminar post (límite write)

### Acciones de Usuario

- `POST /post/{username}/{slug}/like/` - Like a post (límite write: 30/minuto)
- `POST /comment/{pk}/like/` - Like a comment (límite write: 30/minuto)
- `POST /post/{username}/{slug}/favorite/` - Favorito a post (límite write: 30/minuto)
- `POST /upload-image/` - Subir imagen (límite write: 20/minuto)

### Búsqueda

- `GET /search/` - Búsqueda de posts (límite search: 30/minuto)

## Respuestas de Rate Limiting

Cuando se excede un límite de tasa, la API responderá con:

### Para solicitudes JSON/API:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Has excedido el límite de solicitudes permitidas. Por favor, intenta de nuevo más tarde.",
  "retry_after": 60
}
```

Con un código de estado HTTP 429 (Too Many Requests).

### Para solicitudes web normales:

Se mostrará la página de error de rate limit con información sobre cuándo se puede volver a intentar.

## Implementación Técnica

El rate limiting se implementa utilizando:

1. **Decoradores personalizados** para vistas basadas en funciones:
   - `api_rate_limit()` - Límite general para API
   - `search_rate_limit()` - Límite para búsquedas
   - `auth_rate_limit()` - Límite para autenticación
   - `sensitive_rate_limit()` - Límite para datos sensibles
   - `write_rate_limit()` - Límite para operaciones de escritura

2. **Throttling de DRF** para vistas basadas en clases:
   - `CustomUserRateThrottle` - Para usuarios autenticados
   - `CustomAnonRateThrottle` - Para usuarios anónimos

3. **Identificación robusta** de clientes:
   - Para usuarios autenticados: ID de usuario
   - Para usuarios anónimos: Combinación de IP y User-Agent

## Monitoreo y Logging

Todos los eventos de rate limiting se registran en los logs con información detallada:

- IP del cliente
- ID de usuario (si está autenticado)
- Ruta y método de la solicitud
- Grupo de rate limiting
- Número de solicitudes realizadas vs. límite

## Excepciones

Los siguientes usuarios están exentos de rate limiting:

- Superusuarios
- Staff

## Configuración

La configuración de rate limiting se puede ajustar en:

- `blog/api_ratelimit.py` - Configuración general de límites
- `blog/configuraciones/drf_settings.py` - Configuración para DRF