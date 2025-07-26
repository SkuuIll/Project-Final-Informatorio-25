"""
Servicio central para gestión del sistema de tags inteligente.
Integra normalización, recomendaciones y extracción de palabras clave.
"""

from typing import List, Dict, Tuple
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from taggit.models import Tag
from ..models import TagMetadata, TagSynonym, TagCooccurrence, TagUsageHistory
from .tag_normalizer import TagNormalizer
from .keyword_extractor import KeywordExtractor
from .tag_recommender import TagRecommender


class TagManagerService:
    """
    Servicio central para gestión de tags inteligente.
    """
    
    def __init__(self):
        self.normalizer = TagNormalizer()
        self.recommender = TagRecommender()
        self.keyword_extractor = KeywordExtractor()
    
    def suggest_tags(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Sugerencias de autocompletado basadas en popularidad y similitud.
        
        Args:
            query: Consulta de búsqueda
            limit: Número máximo de sugerencias
            
        Returns:
            List[Dict]: Lista de sugerencias con metadatos
        """
        if len(query) < 2:
            return []
        
        suggestions = []
        
        # 1. Búsqueda exacta y por prefijo
        exact_matches = Tag.objects.filter(name__icontains=query).select_related('metadata')[:limit//2]
        
        for tag in exact_matches:
            metadata = getattr(tag, 'metadata', None)
            suggestions.append({
                'name': tag.name,
                'usage_count': metadata.usage_count if metadata else 0,
                'is_trending': metadata.is_trending if metadata else False,
                'category': metadata.category if metadata else '',
                'match_type': 'exact',
                'score': 1.0
            })
        
        # 2. Búsqueda por similitud si no hay suficientes resultados exactos
        if len(suggestions) < limit:
            similar_recs = self.recommender.recommend_by_similarity(query, limit - len(suggestions))
            
            for rec in similar_recs:
                # Evitar duplicados
                if not any(s['name'] == rec['tag'] for s in suggestions):
                    suggestions.append({
                        'name': rec['tag'],
                        'usage_count': rec.get('usage_count', 0),
                        'is_trending': False,
                        'category': '',
                        'match_type': 'similar',
                        'score': rec['score']
                    })
        
        # 3. Ordenar por relevancia
        suggestions.sort(key=lambda x: (x['score'], x['usage_count']), reverse=True)
        
        return suggestions[:limit]
    
    def normalize_tag(self, tag_text: str) -> str:
        """
        Normalización de tags.
        
        Args:
            tag_text: Texto del tag a normalizar
            
        Returns:
            str: Tag normalizado
        """
        return self.normalizer.normalize(tag_text)
    
    def create_or_get_tag(self, tag_text: str, user: User = None) -> Tuple[Tag, bool]:
        """
        Creación inteligente de tags con normalización y validación.
        
        Args:
            tag_text: Texto del tag
            user: Usuario que crea el tag
            
        Returns:
            Tuple[Tag, bool]: (tag, created)
        """
        try:
            # Normalizar tag
            normalized = self.normalizer.normalize(tag_text)
            
            # Verificar forma canónica (sinónimos)
            canonical = self.normalizer.get_canonical_form(normalized)
            
            # Obtener o crear tag
            tag, created = Tag.objects.get_or_create(name=canonical)
            
            # Crear o actualizar metadata
            if created or not hasattr(tag, 'metadata'):
                TagMetadata.optimized.get_or_create_for_tag(tag, user)
            
            return tag, created
            
        except ValidationError as e:
            raise ValidationError(f"Error al crear tag: {str(e)}")
    
    def get_popular_tags(self, limit: int = 20) -> List[Tag]:
        """
        Tags más populares.
        
        Args:
            limit: Número máximo de tags
            
        Returns:
            List[Tag]: Lista de tags populares
        """
        popular_metadata = TagMetadata.optimized.popular(limit)
        return [metadata.tag for metadata in popular_metadata]
    
    def get_trending_tags(self, days: int = 7, limit: int = 10) -> List[Tag]:
        """
        Tags trending basado en uso reciente.
        
        Args:
            days: Días para calcular trending
            limit: Número máximo de tags
            
        Returns:
            List[Tag]: Lista de tags trending
        """
        trending_metadata = TagMetadata.optimized.trending().order_by('-trending_score')[:limit]
        return [metadata.tag for metadata in trending_metadata]
    
    def merge_tags(self, source_tag: Tag, target_tag: Tag, user: User) -> bool:
        """
        Fusión de tags.
        
        Args:
            source_tag: Tag a fusionar (será eliminado)
            target_tag: Tag destino
            user: Usuario que realiza la fusión
            
        Returns:
            bool: True si la fusión fue exitosa
        """
        try:
            with transaction.atomic():
                # Crear sinónimo
                TagSynonym.optimized.create_synonym(target_tag, source_tag.name, user)
                
                # Transferir todas las relaciones
                from taggit.models import TaggedItem
                TaggedItem.objects.filter(tag=source_tag).update(tag=target_tag)
                
                # Actualizar metadata del tag destino
                source_metadata = getattr(source_tag, 'metadata', None)
                target_metadata, _ = TagMetadata.optimized.get_or_create_for_tag(target_tag, user)
                
                if source_metadata:
                    target_metadata.usage_count += source_metadata.usage_count
                    target_metadata.save()
                
                # Actualizar coocurrencias
                TagCooccurrence.objects.filter(tag1=source_tag).update(tag1=target_tag)
                TagCooccurrence.objects.filter(tag2=source_tag).update(tag2=target_tag)
                
                # Actualizar historial
                TagUsageHistory.objects.filter(tag=source_tag).update(tag=target_tag)
                
                # Eliminar tag original
                source_tag.delete()
                
                return True
                
        except Exception as e:
            print(f"Error al fusionar tags: {e}")
            return False
    
    def suggest_related_tags(self, existing_tags: List[str], limit: int = 5) -> List[str]:
        """
        Sugerir tags relacionados basado en coocurrencia.
        
        Args:
            existing_tags: Lista de tags existentes
            limit: Número máximo de sugerencias
            
        Returns:
            List[str]: Lista de tags relacionados
        """
        recommendations = self.recommender.recommend_by_cooccurrence(existing_tags, limit)
        return [rec['tag'] for rec in recommendations]
    
    def extract_keywords_from_content(self, title: str, content: str) -> List[str]:
        """
        Extracción de palabras clave del contenido.
        
        Args:
            title: Título del post
            content: Contenido del post
            
        Returns:
            List[str]: Lista de palabras clave extraídas
        """
        keywords = self.keyword_extractor.extract_from_content(title, content)
        keyword_texts = [kw['keyword'] for kw in keywords[:10]]
        return self.keyword_extractor.suggest_tags_from_keywords(keyword_texts)
    
    def process_post_tags(self, post, tag_names: List[str], user: User) -> List[Tag]:
        """
        Procesa tags para un post (crear, normalizar, actualizar estadísticas).
        
        Args:
            post: Instancia del post
            tag_names: Lista de nombres de tags
            user: Usuario que crea el post
            
        Returns:
            List[Tag]: Lista de tags procesados
        """
        processed_tags = []
        
        with transaction.atomic():
            for tag_name in tag_names:
                try:
                    tag, created = self.create_or_get_tag(tag_name, user)
                    processed_tags.append(tag)
                    
                    # Actualizar estadísticas
                    TagMetadata.optimized.update_usage_count(tag)
                    
                    # Registrar en historial
                    TagUsageHistory.optimized.record_usage(tag, post, user)
                    
                except ValidationError as e:
                    print(f"Error procesando tag '{tag_name}': {e}")
                    continue
            
            # Actualizar matriz de coocurrencia
            if len(processed_tags) > 1:
                self.recommender.update_cooccurrence_matrix([tag.name for tag in processed_tags])
        
        return processed_tags
    
    def get_tag_suggestions_for_post(self, title: str = '', content: str = '', 
                                   existing_tags: List[str] = None, user: User = None) -> Dict:
        """
        Obtiene sugerencias completas para un post.
        
        Args:
            title: Título del post
            content: Contenido del post
            existing_tags: Tags ya seleccionados
            user: Usuario para personalización
            
        Returns:
            Dict: Diccionario con diferentes tipos de sugerencias
        """
        suggestions = {
            'keywords': [],
            'related': [],
            'popular': [],
            'trending': [],
            'mixed': []
        }
        
        # Sugerencias por palabras clave del contenido
        if title or content:
            keyword_suggestions = self.extract_keywords_from_content(title, content)
            suggestions['keywords'] = keyword_suggestions[:8]
        
        # Sugerencias por tags relacionados
        if existing_tags:
            related_suggestions = self.suggest_related_tags(existing_tags, limit=5)
            suggestions['related'] = related_suggestions
        
        # Tags populares
        popular_tags = self.get_popular_tags(limit=10)
        suggestions['popular'] = [tag.name for tag in popular_tags]
        
        # Tags trending
        trending_tags = self.get_trending_tags(limit=8)
        suggestions['trending'] = [tag.name for tag in trending_tags]
        
        # Sugerencias mixtas
        mixed_recs = self.recommender.get_mixed_recommendations(
            existing_tags=existing_tags,
            content=f"{title} {content}",
            user=user,
            limit=10
        )
        suggestions['mixed'] = [rec['tag'] for rec in mixed_recs]
        
        return suggestions
    
    def validate_tag_list(self, tag_names: List[str], max_tags: int = 10) -> Tuple[List[str], List[str]]:
        """
        Valida una lista de tags.
        
        Args:
            tag_names: Lista de nombres de tags
            max_tags: Número máximo de tags permitidos
            
        Returns:
            Tuple[List[str], List[str]]: (tags_válidos, errores)
        """
        valid_tags = []
        errors = []
        
        if len(tag_names) > max_tags:
            errors.append(f"Máximo {max_tags} tags permitidos")
            tag_names = tag_names[:max_tags]
        
        for tag_name in tag_names:
            try:
                normalized = self.normalizer.normalize(tag_name)
                if normalized not in valid_tags:
                    valid_tags.append(normalized)
                else:
                    errors.append(f"Tag duplicado: {tag_name}")
            except ValidationError as e:
                errors.append(f"Tag inválido '{tag_name}': {str(e)}")
        
        return valid_tags, errors
    
    def get_tag_analytics(self, tag: Tag) -> Dict:
        """
        Obtiene analytics para un tag específico.
        
        Args:
            tag: Tag para analizar
            
        Returns:
            Dict: Diccionario con analytics del tag
        """
        metadata = getattr(tag, 'metadata', None)
        
        analytics = {
            'name': tag.name,
            'usage_count': metadata.usage_count if metadata else 0,
            'is_trending': metadata.is_trending if metadata else False,
            'trending_score': metadata.trending_score if metadata else 0.0,
            'category': metadata.category if metadata else '',
            'created_at': metadata.created_at if metadata else None,
            'last_used': metadata.last_used if metadata else None,
        }
        
        # Obtener tags relacionados
        related_tags = TagCooccurrence.optimized.get_related_tags(tag, limit=5)
        analytics['related_tags'] = [
            {
                'name': rel['tag'].name,
                'strength': rel['strength'],
                'count': rel['count']
            }
            for rel in related_tags
        ]
        
        # Obtener sinónimos
        synonyms = TagSynonym.optimized.for_tag(tag)
        analytics['synonyms'] = [syn.synonym_text for syn in synonyms]
        
        return analytics
    
    def cleanup_unused_tags(self, days_threshold: int = 180) -> int:
        """
        Limpia tags no utilizados.
        
        Args:
            days_threshold: Días sin uso para considerar limpieza
            
        Returns:
            int: Número de tags limpiados
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_threshold)
        
        # Encontrar tags sin uso reciente y sin posts asociados
        unused_metadata = TagMetadata.objects.filter(
            last_used__lt=cutoff_date,
            usage_count=0
        )
        
        cleaned_count = 0
        for metadata in unused_metadata:
            # Verificar que realmente no tenga posts asociados
            if not metadata.tag.taggit_taggeditem_items.exists():
                metadata.tag.delete()
                cleaned_count += 1
        
        return cleaned_count