# Design Document

## Overview

El sistema de "me gusta" y "favoritos" requiere correcciones en el backend (vistas de Django) y mejoras en el frontend (JavaScript) para funcionar correctamente. El problema principal identificado es la falta del decorador `@login_required` en las vistas, lo que impide que funcionen correctamente para usuarios autenticados.

## Architecture

### Backend Architecture
- **Views Layer**: Vistas de Django que manejan las acciones de likes y favoritos
- **Models Layer**: Modelos Post y Comment con relaciones ManyToMany para likes y favoritos
- **Authentication Layer**: Sistema de autenticación de Django con decoradores apropiados

### Frontend Architecture
- **JavaScript Modules**: Archivos separados para likes y favoritos
- **AJAX Communication**: Comunicación asíncrona con el backend
- **UI Feedback**: Sistema de notificaciones y estados visuales

## Components and Interfaces

### Backend Components

#### 1. Views (posts/views.py)
**Current Issues:**
- `like_post()`: Falta `@login_required` decorator
- `like_comment()`: Falta `@login_required` decorator  
- `favorite_post()`: Falta `@login_required` decorator

**Required Changes:**
```python
@login_required
@csrf_exempt
@write_rate_limit(rate='30/minute')
def like_post(request, username, slug):
    # Implementation with proper error handling
```

#### 2. URL Patterns (posts/urls.py)
**Current State:** URLs están correctamente definidas
- `/post/<username>/<slug>/like/` → like_post
- `/comment/<pk>/like/` → like_comment
- `/post/<username>/<slug>/favorite/` → favorite_post

#### 3. Models (posts/models.py)
**Current State:** Modelos tienen las relaciones correctas
- `Post.likes` → ManyToManyField(User)
- `Post.favorites` → ManyToManyField(User)
- `Comment.likes` → ManyToManyField(User)

### Frontend Components

#### 1. Likes System (static/js/likes.js)
**Current State:** Implementación completa pero puede tener problemas de inicialización
**Required Improvements:**
- Verificar inicialización correcta
- Mejorar manejo de errores de autenticación
- Asegurar compatibilidad con Feather icons

#### 2. Favorites System (static/js/favorites_simple.js)
**Current State:** Implementación básica
**Required Improvements:**
- Verificar selección correcta de elementos DOM
- Mejorar feedback visual

#### 3. Templates (templates/posts/post_detail.html)
**Current State:** Botones correctamente implementados con atributos necesarios

## Data Models

### Existing Models (No changes required)

```python
class Post(models.Model):
    # ... other fields
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)
    favorites = models.ManyToManyField(User, related_name="favorite_posts", blank=True)

class Comment(models.Model):
    # ... other fields  
    likes = models.ManyToManyField(User, related_name="liked_comments", blank=True)
```

### API Response Format

#### Like/Favorite Success Response
```json
{
    "success": true,
    "liked": true,  // or "favorited": true
    "likes_count": 5,  // or "favorites_count": 3
    "message": "Like agregado correctamente"
}
```

#### Error Response
```json
{
    "success": false,
    "error": "Descripción del error"
}
```

## Error Handling

### Backend Error Handling

#### Authentication Errors
- **401 Unauthorized**: Usuario no autenticado
- **403 Forbidden**: Usuario sin permisos
- **Response**: JSON con mensaje explicativo

#### Resource Errors  
- **404 Not Found**: Post o comentario no existe
- **Response**: JSON con mensaje explicativo

#### Server Errors
- **500 Internal Server Error**: Error del servidor
- **Response**: JSON con mensaje genérico (sin exponer detalles internos)

### Frontend Error Handling

#### Network Errors
- **Connection Failed**: Mostrar mensaje "Error de conexión"
- **Timeout**: Mostrar mensaje "La solicitud tardó demasiado"

#### Authentication Errors
- **401/403**: Mostrar mensaje y redirigir a login después de 1.5 segundos

#### User Experience
- **Loading States**: Deshabilitar botón durante procesamiento
- **Visual Feedback**: Animaciones para confirmar acciones
- **Toast Notifications**: Mensajes temporales para feedback

## Testing Strategy

### Backend Testing

#### Unit Tests for Views
```python
class LikeViewsTestCase(TestCase):
    def test_like_post_requires_authentication(self):
        # Test that unauthenticated users get 401
        
    def test_like_post_toggles_correctly(self):
        # Test like/unlike functionality
        
    def test_like_nonexistent_post_returns_404(self):
        # Test error handling
```

#### Integration Tests
- Test complete like/favorite workflows
- Test rate limiting functionality
- Test CSRF protection

### Frontend Testing

#### Manual Testing Checklist
- [ ] Like button works for authenticated users
- [ ] Like button shows login prompt for anonymous users
- [ ] Like count updates correctly
- [ ] Visual state changes (heart icon fills/unfills)
- [ ] Favorite button works correctly
- [ ] Error messages display properly
- [ ] Loading states work correctly
- [ ] Multiple rapid clicks are handled properly

#### Browser Compatibility
- Test in Chrome, Firefox, Safari, Edge
- Test on mobile devices
- Test with JavaScript disabled (graceful degradation)

## Implementation Plan

### Phase 1: Backend Fixes
1. Add `@login_required` decorators to views
2. Improve error handling in views
3. Add proper logging for debugging
4. Test authentication flow

### Phase 2: Frontend Improvements  
1. Debug JavaScript initialization issues
2. Improve error handling and user feedback
3. Test cross-browser compatibility
4. Optimize performance

### Phase 3: Testing & Validation
1. Write comprehensive tests
2. Manual testing across different scenarios
3. Performance testing
4. Security testing

## Security Considerations

### CSRF Protection
- All POST requests must include CSRF token
- Views use `@csrf_exempt` but validate token in JavaScript

### Rate Limiting
- Current: 30 requests per minute per user
- Prevents abuse of like/favorite functionality

### Input Validation
- Validate post/comment existence before processing
- Validate user permissions
- Sanitize all inputs

### Authentication
- Require authentication for all like/favorite actions
- Proper session management
- Secure cookie handling