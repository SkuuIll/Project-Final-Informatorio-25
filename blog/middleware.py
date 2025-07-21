import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware:
    """
    Middleware para manejo centralizado de errores
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Maneja excepciones no capturadas
        """
        logger.error(
            f"Unhandled exception: {exception}",
            exc_info=True,
            extra={
                'request': request,
                'user': getattr(request, 'user', None),
            }
        )

        # Si es una petición AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Ha ocurrido un error interno. Por favor, inténtalo de nuevo.'
            }, status=500)

        # Para peticiones normales, mostrar página de error
        if settings.DEBUG:
            # En desarrollo, dejar que Django maneje el error
            return None
        else:
            # En producción, mostrar página de error personalizada
            return render(request, '500.html', status=500)

class SecurityHeadersMiddleware:
    """
    Middleware para agregar headers de seguridad
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Agregar headers de seguridad
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy básico
        if not settings.DEBUG:
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self';"
            )
        
        return response