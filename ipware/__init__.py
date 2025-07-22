"""
Módulo para obtener la dirección IP real del cliente.
"""

def get_client_ip(request):
    """
    Obtiene la dirección IP real del cliente, considerando proxies.
    
    Args:
        request: Objeto request de Django
        
    Returns:
        Tupla (ip, is_routable) donde ip es la dirección IP y is_routable indica si es enrutable
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Tomar la primera IP (la del cliente original)
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    
    # Determinar si la IP es enrutable
    is_routable = not (ip.startswith('127.') or ip.startswith('::1') or ip.startswith('fe80:'))
    
    return ip, is_routable