import os
import sys

def main():
    """Run administrative tasks."""
    # Si se está ejecutando el comando 'test', usar la configuración de test.
    # De lo contrario, usar la configuración local por defecto.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog.configuraciones.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()