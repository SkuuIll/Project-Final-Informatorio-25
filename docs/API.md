# DevBlog API Documentation

## Endpoints de Posts

### Listar Posts
- **URL**: `/api/posts/`
- **Método**: `GET`
- **Descripción**: Obtiene una lista de todos los posts publicados
- **Parámetros**: 
  - `page`: Número de página (opcional)
  - `page_size`: Tamaño de página (opcional, máximo 100)

**Respuesta de ejemplo**:
```json
{
  "count": 10,
  "next": "http://localhost:8000/api/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Mi Primer Post",
      "slug": "mi-primer-post",
      "content": "Contenido del post...",
      "author": "admin",
      "created_at": "2024-01-01T12:00:00Z",
      "views": 42,
      "likes_count": 5,
      "tags": ["django", "python"]
    }
  ]
}
```

### Obtener Post Individual
- **URL**: `/api/posts/{slug}/`
- **Método**: `GET`
- **Descripción**: Obtiene un post específico por su slug

### Dar Like a Post
- **URL**: `/post/{username}/{slug}/like/`
- **Método**: `POST`
- **Descripción**: Permite dar o quitar like a un post
- **Autenticación**: Requerida
- **Headers**: 
  - `X-CSRFToken`: Token CSRF
  - `X-Requested-With`: `XMLHttpRequest`

**Respuesta de ejemplo**:
```json
{
  "success": true,
  "liked": true,
  "likes_count": 6,
  "message": "Like agregado correctamente"
}
```

### Agregar a Favoritos
- **URL**: `/post/{username}/{slug}/favorite/`
- **Método**: `POST`
- **Descripción**: Permite agregar o quitar un post de favoritos
- **Autenticación**: Requerida

**Respuesta de ejemplo**:
```json
{
  "success": true,
  "favorited": true,
  "favorites_count": 3,
  "message": "Agregado a favoritos"
}
```

## Endpoints de Comentarios

### Dar Like a Comentario
- **URL**: `/comment/{id}/like/`
- **Método**: `POST`
- **Descripción**: Permite dar o quitar like a un comentario
- **Autenticación**: Requerida

**Respuesta de ejemplo**:
```json
{
  "success": true,
  "liked": true,
  "likes_count": 2,
  "message": "Like agregado al comentario"
}
```

## Códigos de Error

- `400`: Petición incorrecta
- `401`: No autenticado
- `403`: Sin permisos
- `404`: Recurso no encontrado
- `405`: Método no permitido
- `500`: Error interno del servidor

## Autenticación

La API utiliza autenticación basada en sesiones de Django. Para endpoints que requieren autenticación, el usuario debe estar logueado en el sitio web.

## Rate Limiting

Actualmente no hay límites de velocidad implementados, pero se recomienda no hacer más de 100 peticiones por minuto.

## Versionado

La API actualmente no tiene versionado. Todos los endpoints están en la versión base.