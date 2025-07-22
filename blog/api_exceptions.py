"""
Manejadores de excepciones personalizados para la API.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework import status
from django.utils.translation import gettext as _

logger = logging.getLogger('django.security')

def custom_exception_handler(exc, context):
    """
    Manejador de excepciones personalizado para la API.
    Proporciona respuestas más detalladas y registra errores importantes.
    """
    # Primero, obtener la respuesta estándar de DRF
    response = exception_handler(exc, context)
    
    # Si es una excepción de throttling, personalizar la respuesta
    if isinstance(exc, Throttled):
        custom_response_data = {
            'error': 'rate_limit_exceeded',
            'message': _('Has excedido el límite de solicitudes permitidas. Por favor, intenta de nuevo más tarde.'),
            'retry_after': exc.wait,
        }
        
        # Registrar el intento de abuso
        request = context['request']
        logger.warning(
            f"Rate limit excedido en API: {request.method} {request.path}",
            extra={
                'ip': _get_client_ip(request),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'path': request.path,
                'method': request.method,
                'wait': exc.wait,
            }
        )
        
        if response is None:
            response = Response(custom_response_data, status=status.HTTP_429_TOO_MANY_REQUESTS)
        else:
            response.data = custom_response_data
    
    # Si no hay respuesta (excepción no manejada), crear una respuesta genérica
    if response is None:
        # Registrar la excepción no manejada
        logger.error(
            f"Excepción no manejada en API: {exc}",
            exc_info=True,
            extra={
                'view': context['view'].__class__.__name__ if 'view' in context else 'unknown',
                'request_path': context['request'].path if 'request' in context else 'unknown',
            }
        )
        
        response = Response(
            {'error': 'internal_server_error', 'message': _('Ha ocurrido un error interno.')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response

def _get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente, considerando proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Tomar la primera IP (la del cliente original)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip