"""
Comando para probar la generación de imágenes de portada.
"""

from django.core.management.base import BaseCommand
from posts.image_generation import registry
from posts.prompt_manager import PromptManager


class Command(BaseCommand):
    help = 'Prueba la generación de imágenes de portada'

    def add_arguments(self, parser):
        parser.add_argument(
            '--service',
            type=str,
            default='gemini',
            help='Servicio de generación de imágenes a usar (por defecto: gemini)',
        )
        parser.add_argument(
            '--title',
            type=str,
            default='Introducción a la Inteligencia Artificial',
            help='Título del post para la imagen',
        )
        parser.add_argument(
            '--style',
            type=str,
            default='professional',
            help='Estilo de la imagen (professional, modern, tech, creative)',
        )

    def handle(self, *args, **options):
        service_name = options['service']
        title = options['title']
        style = options['style']
        
        self.stdout.write(f'🎨 Probando generación de imagen de portada...')
        self.stdout.write(f'   - Servicio: {service_name}')
        self.stdout.write(f'   - Título: {title}')
        self.stdout.write(f'   - Estilo: {style}')
        
        # Verificar servicios disponibles
        available_services = registry.get_available_services()
        self.stdout.write(f'📋 Servicios disponibles: {available_services}')
        
        if service_name not in available_services:
            self.stdout.write(
                self.style.ERROR(f'❌ Servicio "{service_name}" no disponible')
            )
            return
        
        # Obtener servicio
        service = registry.get_service(service_name)
        if not service:
            self.stdout.write(
                self.style.ERROR(f'❌ No se pudo obtener el servicio "{service_name}"')
            )
            return
        
        self.stdout.write(f'✅ Servicio {service.get_service_name()} obtenido')
        
        # Obtener prompt personalizado
        try:
            image_prompt_template = PromptManager.get_default_prompt('image')
            
            # Formatear el prompt
            cover_prompt = image_prompt_template.format(
                title=title,
                keywords='inteligencia artificial, machine learning, tecnología',
                style=style,
                size='1024x1024'
            )
            
            self.stdout.write(f'📝 Prompt generado:')
            self.stdout.write(f'   {cover_prompt[:200]}...')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Error al formatear prompt personalizado: {e}')
            )
            cover_prompt = f"Create a professional blog post cover image about: {title}"
        
        # Generar imagen
        self.stdout.write('🚀 Generando imagen...')
        
        try:
            success, image_url, error = service.generate_image(
                cover_prompt,
                style=style,
                size='1024x1024',
                allow_placeholder=True
            )
            
            if success and image_url:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Imagen generada exitosamente!')
                )
                self.stdout.write(f'   URL: {image_url}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error al generar imagen: {error}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'💥 Error crítico: {e}')
            )
            import traceback
            traceback.print_exc()
        
        # Información adicional del servicio
        self.stdout.write('\n📊 Información del servicio:')
        try:
            params = service.get_supported_parameters()
            self.stdout.write(f'   Parámetros soportados: {list(params.keys())}')
            
            cost = service.get_cost_estimate()
            self.stdout.write(f'   Costo estimado: ${cost}')
            
            time_est = service.get_generation_time_estimate()
            self.stdout.write(f'   Tiempo estimado: {time_est}s')
            
        except Exception as e:
            self.stdout.write(f'   Error obteniendo información: {e}')