"""
Sistema de recomendaciones basado en estadísticas para tags.
Proporciona recomendaciones por coocurrencia, similitud y popularidad.
"""

from typing import List, Dict
from django.db.models import Q, Count, F
from taggit.models import Tag
from ..models import TagCooccurrence, TagMetadata, TagUsageHistory
from .tag_normalizer import TagNormalizer


class TagRecommender:
    """
    Sistema de recomendaciones basado en estadísticas.
    """
    
    def __init__(self):
        self.normalizer = TagNormalizer()
    
    def recommend_by_cooccurrence(self, existing_tags: List[str], limit: int = 5) -> List[Dict]:
        """
        Recomienda tags basado en coocurrencia con tags existentes.
        
        Args:
            existing_tags: Lista de nombres de tags existentes
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista de recomendaciones con scores
        """
        if not existing_tags:
            return []
        
        # Obtener objetos Tag
        tag_objects = Tag.objects.filter(name__in=existing_tags)
        if not tag_objects.exists():
            return []
        
        # Buscar coocurrencias
        recommendations = {}
        
        for tag in tag_objects:
            # Buscar coocurrencias donde este tag es tag1 o tag2
            cooccurrences = TagCooccurrence.optimized.for_tag(tag).strong_relations().ordered_by_strength()[:limit * 2]
            
            for cooccurrence in cooccurrences:
                # Determinar el tag relacionado
                related_tag = cooccurrence.tag2 if cooccurrence.tag1 == tag else cooccurrence.tag1
                
                # No recomendar tags que ya están en la lista
                if related_tag.name in existing_tags:
                    continue
                
                # Acumular scores
                if related_tag.name in recommendations:
                    recommendations[related_tag.name]['score'] += cooccurrence.strength
                    recommendations[related_tag.name]['count'] += cooccurrence.count
                else:
                    recommendations[related_tag.name] = {
                        'tag': related_tag.name,
                        'score': cooccurrence.strength,
                        'count': cooccurrence.count,
                        'reason': 'coocurrencia'
                    }
        
        # Ordenar por score y limitar
        sorted_recommendations = sorted(
            recommendations.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:limit]
        
        return sorted_recommendations
    
    def recommend_by_similarity(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recomienda tags similares usando distancia de strings.
        
        Args:
            query: Texto de consulta
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista de tags similares con scores
        """
        if len(query) < 2:
            return []
        
        # Usar el normalizador para encontrar tags similares
        similar_tags = self.normalizer.find_similar_tags(query, threshold=0.6)
        
        recommendations = []
        for tag in similar_tags[:limit]:
            # Obtener metadata si existe
            metadata = getattr(tag, 'metadata', None)
            
            recommendations.append({
                'tag': tag.name,
                'score': self.normalizer._calculate_similarity(query.lower(), tag.name.lower()),
                'usage_count': metadata.usage_count if metadata else 0,
                'reason': 'similitud'
            })
        
        return recommendations
    
    def recommend_by_popularity(self, category: str = None, limit: int = 10) -> List[Dict]:
        """
        Recomienda tags populares.
        
        Args:
            category: Categoría específica (opcional)
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista de tags populares
        """
        if category:
            popular_metadata = TagMetadata.optimized.by_category(category).popular(limit)
        else:
            popular_metadata = TagMetadata.optimized.popular(limit)
        
        recommendations = []
        for metadata in popular_metadata:
            recommendations.append({
                'tag': metadata.tag.name,
                'score': metadata.usage_count / 100.0,  # Normalizar score
                'usage_count': metadata.usage_count,
                'category': metadata.category,
                'is_trending': metadata.is_trending,
                'reason': 'popularidad'
            })
        
        return recommendations
    
    def recommend_by_user_history(self, user, limit: int = 5) -> List[Dict]:
        """
        Recomienda basado en historial del usuario.
        
        Args:
            user: Usuario para el que recomendar
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista de recomendaciones basadas en historial
        """
        if not user.is_authenticated:
            return []
        
        # Obtener tags más usados por el usuario
        user_tags = TagUsageHistory.optimized.for_user(user).values('tag').annotate(
            usage_count=Count('tag')
        ).order_by('-usage_count')[:10]
        
        if not user_tags:
            return []
        
        # Obtener nombres de tags
        user_tag_names = []
        for tag_data in user_tags:
            tag = Tag.objects.get(id=tag_data['tag'])
            user_tag_names.append(tag.name)
        
        # Recomendar basado en coocurrencia con tags del usuario
        return self.recommend_by_cooccurrence(user_tag_names, limit)
    
    def calculate_tag_similarity(self, tag1: str, tag2: str) -> float:
        """
        Calcula similitud entre dos tags.
        
        Args:
            tag1: Primer tag
            tag2: Segundo tag
            
        Returns:
            float: Similitud entre 0 y 1
        """
        return self.normalizer._calculate_similarity(tag1.lower(), tag2.lower())
    
    def update_cooccurrence_matrix(self, tags: List[str]) -> None:
        """
        Actualiza matriz de coocurrencia cuando se crea un post.
        
        Args:
            tags: Lista de nombres de tags del post
        """
        if len(tags) < 2:
            return
        
        # Obtener objetos Tag
        tag_objects = Tag.objects.filter(name__in=tags)
        
        # Actualizar coocurrencias usando el manager
        TagCooccurrence.optimized.update_from_post_tags(tag_objects)
    
    def get_trending_recommendations(self, days: int = 7, limit: int = 10) -> List[Dict]:
        """
        Obtiene recomendaciones de tags trending.
        
        Args:
            days: Días para calcular trending
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista de tags trending
        """
        trending_metadata = TagMetadata.optimized.trending().order_by('-trending_score')[:limit]
        
        recommendations = []
        for metadata in trending_metadata:
            recommendations.append({
                'tag': metadata.tag.name,
                'score': metadata.trending_score,
                'usage_count': metadata.usage_count,
                'category': metadata.category,
                'reason': 'trending'
            })
        
        return recommendations
    
    def get_category_recommendations(self, content: str, limit: int = 5) -> List[Dict]:
        """
        Recomienda tags basado en categorización del contenido.
        
        Args:
            content: Contenido a analizar
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista de recomendaciones por categoría
        """
        # Palabras clave por categoría
        category_keywords = {
            'programación': ['código', 'programar', 'desarrollo', 'software', 'algoritmo'],
            'web': ['html', 'css', 'javascript', 'frontend', 'backend', 'api'],
            'base-de-datos': ['sql', 'database', 'datos', 'consulta', 'tabla'],
            'devops': ['docker', 'kubernetes', 'deployment', 'servidor', 'infraestructura'],
            'móvil': ['android', 'ios', 'app', 'móvil', 'aplicación'],
            'ia': ['inteligencia', 'artificial', 'machine', 'learning', 'neural']
        }
        
        content_lower = content.lower()
        category_scores = {}
        
        # Calcular scores por categoría
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                category_scores[category] = score
        
        # Obtener recomendaciones de las categorías más relevantes
        recommendations = []
        for category, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
            category_recs = self.recommend_by_popularity(category, limit=3)
            for rec in category_recs:
                rec['category_score'] = score
                recommendations.append(rec)
        
        return recommendations[:limit]
    
    def get_mixed_recommendations(self, existing_tags: List[str] = None, 
                                content: str = None, user=None, limit: int = 10) -> List[Dict]:
        """
        Obtiene recomendaciones mixtas usando múltiples estrategias.
        
        Args:
            existing_tags: Tags ya seleccionados
            content: Contenido para análisis
            user: Usuario para personalización
            limit: Número máximo de recomendaciones
            
        Returns:
            List[Dict]: Lista mixta de recomendaciones
        """
        all_recommendations = {}
        
        # Recomendaciones por coocurrencia
        if existing_tags:
            cooccurrence_recs = self.recommend_by_cooccurrence(existing_tags, limit=5)
            for rec in cooccurrence_recs:
                rec['weight'] = 0.4  # Peso alto para coocurrencia
                all_recommendations[rec['tag']] = rec
        
        # Recomendaciones por historial de usuario
        if user:
            user_recs = self.recommend_by_user_history(user, limit=3)
            for rec in user_recs:
                if rec['tag'] not in all_recommendations:
                    rec['weight'] = 0.3
                    all_recommendations[rec['tag']] = rec
                else:
                    all_recommendations[rec['tag']]['score'] += rec['score'] * 0.3
        
        # Recomendaciones por categoría de contenido
        if content:
            category_recs = self.get_category_recommendations(content, limit=3)
            for rec in category_recs:
                if rec['tag'] not in all_recommendations:
                    rec['weight'] = 0.2
                    all_recommendations[rec['tag']] = rec
                else:
                    all_recommendations[rec['tag']]['score'] += rec['score'] * 0.2
        
        # Recomendaciones trending
        trending_recs = self.get_trending_recommendations(limit=3)
        for rec in trending_recs:
            if rec['tag'] not in all_recommendations:
                rec['weight'] = 0.1
                all_recommendations[rec['tag']] = rec
            else:
                all_recommendations[rec['tag']]['score'] += rec['score'] * 0.1
        
        # Ordenar por score final y limitar
        final_recommendations = sorted(
            all_recommendations.values(),
            key=lambda x: x['score'],
            reverse=True
        )[:limit]
        
        return final_recommendations