"""
Comando de management para inicializar el sistema de tags inteligente.
Crea metadatos para tags existentes y calcula estadísticas iniciales.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from taggit.models import Tag, TaggedItem
from posts.models import TagMetadata, TagCooccurrence, TagUsageHistory, Post
from collections import defaultdict, Counter
import math


class Command(BaseCommand):
    help = 'Inicializa el sistema de tags inteligente con datos existentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreación de metadatos existentes',
        )
        parser.add_argument(
            '--calculate-cooccurrence',
            action='store_true',
            help='Calcula matriz de coocurrencia basada en posts existentes',
        )
        parser.add_argument(
            '--create-history',
            action='store_true',
            help='Crea historial de uso basado en posts existentes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Inicializando sistema de tags inteligente...')
        )

        try:
            with transaction.atomic():
                # 1. Crear metadatos para tags existentes
                self.create_tag_metadata(force=options['force'])
                
                # 2. Calcular matriz de coocurrencia si se solicita
                if options['calculate_cooccurrence']:
                    self.calculate_cooccurrence_matrix()
                
                # 3. Crear historial de uso si se solicita
                if options['create_history']:
                    self.create_usage_history()
                
                # 4. Calcular trending scores
                self.calculate_trending_scores()

            self.stdout.write(
                self.style.SUCCESS('✅ Sistema de tags inteligente inicializado correctamente')
            )

        except Exception as e:
            raise CommandError(f'Error al inicializar sistema de tags: {str(e)}')

    def create_tag_metadata(self, force=False):
        """Crea metadatos para todos los tags existentes."""
        self.stdout.write('📊 Creando metadatos de tags...')
        
        tags = Tag.objects.all()
        created_count = 0
        updated_count = 0
        
        for tag in tags:
            # Calcular uso real del tag
            usage_count = TaggedItem.objects.filter(tag=tag).count()
            
            # Obtener o crear metadata
            metadata, created = TagMetadata.objects.get_or_create(
                tag=tag,
                defaults={
                    'usage_count': usage_count,
                    'trending_score': 0.0,
                    'is_approved': True,
                    'is_trending': False,
                    'category': self.categorize_tag(tag.name),
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Creado metadata para: {tag.name}')
            elif force:
                # Actualizar si se fuerza
                metadata.usage_count = usage_count
                metadata.category = self.categorize_tag(tag.name)
                metadata.save()
                updated_count += 1
                self.stdout.write(f'  ↻ Actualizado metadata para: {tag.name}')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'📊 Metadatos creados: {created_count}, actualizados: {updated_count}'
            )
        )

    def calculate_cooccurrence_matrix(self):
        """Calcula la matriz de coocurrencia basada en posts existentes."""
        self.stdout.write('🔗 Calculando matriz de coocurrencia...')
        
        # Limpiar coocurrencias existentes
        TagCooccurrence.objects.all().delete()
        
        posts = Post.objects.filter(status='published').prefetch_related('tags')
        cooccurrence_counts = defaultdict(int)
        
        for post in posts:
            tags = list(post.tags.all())
            
            # Crear pares de tags para este post
            for i, tag1 in enumerate(tags):
                for tag2 in tags[i+1:]:
                    # Asegurar orden consistente
                    if tag1.id > tag2.id:
                        tag1, tag2 = tag2, tag1
                    
                    cooccurrence_counts[(tag1.id, tag2.id)] += 1
        
        # Crear objetos TagCooccurrence
        created_count = 0
        for (tag1_id, tag2_id), count in cooccurrence_counts.items():
            tag1 = Tag.objects.get(id=tag1_id)
            tag2 = Tag.objects.get(id=tag2_id)
            
            # Calcular strength
            tag1_usage = getattr(tag1, 'metadata', None)
            tag2_usage = getattr(tag2, 'metadata', None)
            
            if tag1_usage and tag2_usage:
                strength = count / math.sqrt(tag1_usage.usage_count * tag2_usage.usage_count)
                strength = min(strength, 1.0)
            else:
                strength = 0.0
            
            TagCooccurrence.objects.create(
                tag1=tag1,
                tag2=tag2,
                count=count,
                strength=strength
            )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'🔗 Creadas {created_count} relaciones de coocurrencia')
        )

    def create_usage_history(self):
        """Crea historial de uso basado en posts existentes."""
        self.stdout.write('📈 Creando historial de uso...')
        
        # Limpiar historial existente
        TagUsageHistory.objects.all().delete()
        
        posts = Post.objects.filter(status='published').prefetch_related('tags').select_related('author')
        created_count = 0
        
        for post in posts:
            for tag in post.tags.all():
                TagUsageHistory.objects.create(
                    tag=tag,
                    post=post,
                    user=post.author
                )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'📈 Creados {created_count} registros de historial')
        )

    def calculate_trending_scores(self):
        """Calcula trending scores para todos los tags."""
        self.stdout.write('📊 Calculando trending scores...')
        
        # Usar el manager para calcular trending
        TagMetadata.optimized.calculate_trending_scores(days=7)
        
        trending_count = TagMetadata.objects.filter(is_trending=True).count()
        
        self.stdout.write(
            self.style.SUCCESS(f'📊 {trending_count} tags marcados como trending')
        )

    def categorize_tag(self, tag_name):
        """Categoriza un tag basado en su nombre."""
        tag_lower = tag_name.lower()
        
        # Categorías técnicas
        tech_keywords = {
            'programación': ['python', 'javascript', 'java', 'c++', 'php', 'ruby', 'go', 'rust'],
            'web': ['html', 'css', 'react', 'vue', 'angular', 'django', 'flask', 'node'],
            'base-de-datos': ['sql', 'mysql', 'postgresql', 'mongodb', 'redis'],
            'devops': ['docker', 'kubernetes', 'aws', 'azure', 'jenkins', 'git'],
            'móvil': ['android', 'ios', 'flutter', 'react-native'],
            'ia': ['machine-learning', 'ai', 'tensorflow', 'pytorch', 'deep-learning'],
        }
        
        for category, keywords in tech_keywords.items():
            if any(keyword in tag_lower for keyword in keywords):
                return category
        
        return ''  # Sin categoría específica