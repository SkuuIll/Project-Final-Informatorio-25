"""
Comando para inicializar los prompts por defecto del sistema.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from posts.prompt_manager import initialize_default_prompts


class Command(BaseCommand):
    help = 'Inicializa los prompts por defecto del sistema de IA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username del usuario que creará los prompts (por defecto: primer superuser)',
        )

    def handle(self, *args, **options):
        # Obtener usuario
        username = options.get('user')
        
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Usuario "{username}" no encontrado')
                )
                return
        else:
            # Usar el primer superuser disponible
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(
                    self.style.ERROR('No se encontró ningún superuser. Crea uno primero.')
                )
                return

        self.stdout.write(f'Inicializando prompts por defecto con usuario: {user.username}')
        
        try:
            initialize_default_prompts(user)
            self.stdout.write(
                self.style.SUCCESS('Prompts por defecto inicializados exitosamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error al inicializar prompts: {e}')
            )