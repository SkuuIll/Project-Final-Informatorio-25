"""
Comando para actualizar los prompts existentes con las versiones mejoradas.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from posts.models import AIPromptTemplate
from posts.prompt_manager import PromptManager


class Command(BaseCommand):
    help = 'Actualiza los prompts existentes con las versiones mejoradas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar actualización incluso si los prompts han sido modificados',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Crear backup de los prompts actuales antes de actualizar',
        )

    def handle(self, *args, **options):
        force = options.get('force', False)
        backup = options.get('backup', False)
        
        # Obtener primer superuser para crear backups
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stdout.write(
                self.style.ERROR('No se encontró ningún superuser.')
            )
            return

        prompt_types = ['content', 'tags', 'image']
        updated_count = 0
        
        for prompt_type in prompt_types:
            try:
                # Buscar prompt por defecto existente
                existing_prompt = AIPromptTemplate.objects.filter(
                    prompt_type=prompt_type,
                    is_default=True
                ).first()
                
                if existing_prompt:
                    # Crear backup si se solicita
                    if backup:
                        backup_name = f"{existing_prompt.name} - Backup {existing_prompt.updated_at.strftime('%Y%m%d_%H%M%S')}"
                        AIPromptTemplate.objects.create(
                            name=backup_name,
                            prompt_type=prompt_type,
                            template=existing_prompt.template,
                            description=f"Backup automático de: {existing_prompt.description}",
                            is_default=False,
                            created_by=user
                        )
                        self.stdout.write(f'Backup creado: {backup_name}')
                    
                    # Obtener nuevo template mejorado
                    new_template = PromptManager._get_fallback_prompt(prompt_type)
                    
                    # Verificar si el template ha cambiado
                    if existing_prompt.template != new_template or force:
                        # Actualizar el prompt
                        existing_prompt.template = new_template
                        existing_prompt.name = f"Prompt mejorado - {prompt_type.title()}"
                        existing_prompt.description = f"Prompt mejorado del sistema para {prompt_type} con Gemini 2.0 Flash"
                        existing_prompt.save()
                        
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'Prompt {prompt_type} actualizado exitosamente')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Prompt {prompt_type} no necesita actualización')
                        )
                else:
                    # Crear nuevo prompt si no existe
                    new_template = PromptManager._get_fallback_prompt(prompt_type)
                    PromptManager.create_prompt(
                        name=f"Prompt mejorado - {prompt_type.title()}",
                        prompt_type=prompt_type,
                        template=new_template,
                        user=user,
                        description=f"Prompt mejorado del sistema para {prompt_type} con Gemini 2.0 Flash",
                        is_default=True
                    )
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Prompt {prompt_type} creado exitosamente')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error actualizando prompt {prompt_type}: {e}')
                )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Se actualizaron {updated_count} prompts exitosamente')
            )
        else:
            self.stdout.write(
                self.style.WARNING('No se actualizó ningún prompt')
            )
            
        # Información adicional
        self.stdout.write('\n' + '='*50)
        self.stdout.write('MEJORAS IMPLEMENTADAS:')
        self.stdout.write('• Modelo actualizado a Gemini 2.0 Flash Experimental')
        self.stdout.write('• Prompts de contenido más engaging y estructurados')
        self.stdout.write('• Sistema de tags optimizado para SEO')
        self.stdout.write('• Prompts de imagen más detallados y profesionales')
        self.stdout.write('='*50)