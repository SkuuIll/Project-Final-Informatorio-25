"""
Middleware para la aplicación DevBlog.
"""
import logging
from django.http import HttpResponseServerError
from django.template.response import TemplateResponse

logger = logging.getLogger('django.request')

class SecurityHeadersMiddleware:
    """
    Middleware para agregar cabeceras de seguridad a las respuestas.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar cabeceras de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Agregar Content-Security-Policy en producción
        if not request.META.get('HTTP_HOST', '').startswith(('localhost', '127.0.0.1')):
            csp_directives = [
                "default-src 'self'",
                "img-src 'self' data: https://secure.gravatar.com",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
            ]
            response['Content-Security-Policy'] = '; '.join(csp_directives)
        
        return response

class ErrorHandlingMiddleware:
    """
    Middleware para manejar errores de forma centralizada.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        return self.get_response(request)
    
    def process_exception(self, request, exception):
        """
        Procesa excepciones no manejadas.
        """
        # Registrar la excepción
        logger.exception(
            f"Error no manejado: {exception}",
            extra={
                'path': request.path,
                'method': request.method,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
            }
        )
        
        # Responder con una página de error amigable
        context = {
            'error_message': str(exception),
            'error_type': exception.__class__.__name__,
        }
        
        return TemplateResponse(
            request=request,
            template='500.html',
            context=context,
            status=500
        )