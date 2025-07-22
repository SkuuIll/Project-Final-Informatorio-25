"""
Vistas y utilidades para django-axes.
"""

import logging
from django.shortcuts import render
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta
from axes.utils import reset
from axes.models import AccessAttempt
from blog.ratelimit import get_client_ip

logger = logging.getLogger('django.security')

def locked_out(request, credentials=None):
    """
    Vista para mostrar cuando una cuenta está bloqueada por intentos fallidos.
    """
    ip = get_client_ip(request)
    
    # Registrar el bloqueo
    logger.warning(
        f"Cuenta bloqueada por intentos fallidos de login",
        extra={
            'ip': ip,
            'username': credentials.get('username', 'unknown') if credentials else 'unknown',
        }
    )
    
    # Obtener información del bloqueo
    try:
        attempts = AccessAttempt.objects.filter(
            ip_address=ip
        ).order_by('-attempt_time').first()
        
        if attempts:
            cooloff_time = attempts.attempt_time + timedelta(hours=1)
            time_remaining = cooloff_time - timezone.now()
            minutes_remaining = max(0, time_remaining.seconds // 60)
        else:
            minutes_remaining = 60
    except Exception:
        minutes_remaining = 60
    
    # Responder según el tipo de solicitud
    if request.headers.get('Accept') == 'application/json' or request.path.startswith('/api/'):
        from django.http import JsonResponse
        return JsonResponse({
            'error': 'Account locked',
            'message': _('Tu cuenta ha sido bloqueada temporalmente por demasiados intentos fallidos de inicio de sesión.'),
            'minutes_remaining': minutes_remaining,
        }, status=403)
    
    # Para solicitudes normales, mostrar página de error
    return render(request, 'accounts/locked_out.html', {
        'minutes_remaining': minutes_remaining,
    }, status=403)

def reset_lockout_view(request, username=None):
    """
    Vista para administradores para desbloquear cuentas.
    """
    if not request.user.is_staff:
        return HttpResponse(_("No tienes permiso para realizar esta acción."), status=403)
    
    if username:
        reset(username=username)
        logger.info(
            f"Bloqueo de cuenta reseteado por administrador",
            extra={
                'admin_user': request.user.username,
                'target_user': username,
            }
        )
        return HttpResponse(_("Bloqueo de cuenta reseteado correctamente."))
    
    ip = request.GET.get('ip')
    if ip:
        reset(ip=ip)
        logger.info(
            f"Bloqueo de IP reseteado por administrador",
            extra={
                'admin_user': request.user.username,
                'target_ip': ip,
            }
        )
        return HttpResponse(_("Bloqueo de IP reseteado correctamente."))
    
    return HttpResponse(_("Se requiere un nombre de usuario o IP."), status=400)