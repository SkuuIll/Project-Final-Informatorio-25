from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.contrib.auth import get_user_model
from axes.models import AccessAttempt, AccessLog
from axes.utils import reset
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Gestiona los intentos de acceso y bloqueos de django-axes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset-user',
            help='Resetea los intentos de acceso para un usuario específico',
        )
        parser.add_argument(
            '--reset-ip',
            help='Resetea los intentos de acceso para una IP específica',
        )
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Resetea todos los intentos de acceso',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista los intentos de acceso fallidos',
        )
        parser.add_argument(
            '--list-blocked',
            action='store_true',
            help='Lista los usuarios/IPs bloqueados actualmente',
        )
        parser.add_argument(
            '--clean-old',
            action='store_true',
            help='Limpia los intentos de acceso antiguos',
        )

    def handle(self, *args, **options):
        if options['reset_user']:
            self.reset_user(options['reset_user'])
        elif options['reset_ip']:
            self.reset_ip(options['reset_ip'])
        elif options['reset_all']:
            self.reset_all()
        elif options['list']:
            self.list_attempts()
        elif options['list_blocked']:
            self.list_blocked()
        elif options['clean_old']:
            self.clean_old()
        else:
            self.stdout.write(self.style.WARNING('No se especificó ninguna acción. Use --help para ver las opciones.'))

    def reset_user(self, username):
        try:
            user = User.objects.get(username=username)
            reset(username=username)
            self.stdout.write(self.style.SUCCESS(f'Reseteo exitoso para el usuario {username}'))
        except User.DoesNotExist:
            raise CommandError(f'Usuario {username} no encontrado')

    def reset_ip(self, ip):
        reset(ip=ip)
        self.stdout.write(self.style.SUCCESS(f'Reseteo exitoso para la IP {ip}'))

    def reset_all(self):
        AccessAttempt.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Todos los intentos de acceso han sido reseteados'))

    def list_attempts(self):
        attempts = AccessAttempt.objects.all().order_by('-attempt_time')
        
        if not attempts:
            self.stdout.write('No hay intentos de acceso registrados')
            return
            
        self.stdout.write(self.style.NOTICE('Intentos de acceso fallidos:'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'{"Usuario":<20} {"IP":<15} {"Intentos":<8} {"Último intento":<20} {"Bloqueado":<10}')
        self.stdout.write('-' * 80)
        
        for attempt in attempts:
            is_blocked = "Sí" if attempt.failures_since_start >= 5 else "No"
            self.stdout.write(
                f'{attempt.username:<20} {attempt.ip_address:<15} {attempt.failures_since_start:<8} '
                f'{attempt.attempt_time.strftime("%Y-%m-%d %H:%M:%S"):<20} {is_blocked:<10}'
            )

    def list_blocked(self):
        now = timezone.now()
        cooloff_time = datetime.timedelta(hours=1)  # Ajustar según AXES_COOLOFF_TIME
        
        blocked = AccessAttempt.objects.filter(
            failures_since_start__gte=5,
            attempt_time__gt=now - cooloff_time
        ).order_by('-attempt_time')
        
        if not blocked:
            self.stdout.write('No hay usuarios/IPs bloqueados actualmente')
            return
            
        self.stdout.write(self.style.NOTICE('Usuarios/IPs bloqueados:'))
        self.stdout.write('=' * 80)
        self.stdout.write(f'{"Usuario":<20} {"IP":<15} {"Intentos":<8} {"Bloqueado desde":<20} {"Desbloqueo en":<20}')
        self.stdout.write('-' * 80)
        
        for block in blocked:
            unblock_time = block.attempt_time + cooloff_time
            time_left = unblock_time - now
            
            self.stdout.write(
                f'{block.username:<20} {block.ip_address:<15} {block.failures_since_start:<8} '
                f'{block.attempt_time.strftime("%Y-%m-%d %H:%M:%S"):<20} '
                f'{unblock_time.strftime("%Y-%m-%d %H:%M:%S"):<20}'
            )
            self.stdout.write(f'  Tiempo restante: {time_left}')

    def clean_old(self):
        # Eliminar intentos más antiguos que 30 días
        cutoff = timezone.now() - datetime.timedelta(days=30)
        count, _ = AccessAttempt.objects.filter(attempt_time__lt=cutoff).delete()
        
        # Eliminar logs más antiguos que 90 días
        log_cutoff = timezone.now() - datetime.timedelta(days=90)
        log_count, _ = AccessLog.objects.filter(attempt_time__lt=log_cutoff).delete()
        
        self.stdout.write(self.style.SUCCESS(
            f'Se eliminaron {count} intentos antiguos y {log_count} logs antiguos'
        ))