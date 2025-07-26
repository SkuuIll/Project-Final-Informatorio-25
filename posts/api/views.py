"""
API views para el sistema de tags inteligente.
"""

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from taggit.models import Tag
from ..models import TagMetadata
from ..services import TagManagerService, KeywordExtractor, TagNormalizer
from blog.ratelimit import api_rate_limit


class TagSuggestView(View):
    """API para sugerencias de tags con autocompletado."""
    
    @method_decorator(api_rate_limit)
    def get(self, request):
        query = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 10)), 20)
        
        if len(query) < 2:
            return JsonResponse({'suggestions': []})
        
        # Intentar obtener desde caché
        cache_key = f'tag_suggestions:{query}:{limit}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'suggestions': cached_result})
        
        try:
            manager = TagManagerService()
            suggestions = manager.suggest_tags(query, limit)
            
            # Formatear respuesta
            formatted_suggestions = []
            for suggestion in suggestions:
                if isinstance(suggestion, dict):
                    formatted_suggestions.append(suggestion)
                else:
                    # Si es un objeto Tag
                    metadata = getattr(suggestion, 'metadata', None)
                    formatted_suggestions.append({
                        'name': suggestion.name,
                        'usage_count': metadata.usage_count if metadata else 0,
                        'is_trending': metadata.is_trending if metadata else False,
                        'category': metadata.category if metadata else '',
                    })
            
            # Guardar en caché por 5 minutos
            cache.set(cache_key, formatted_suggestions, 300)
            
            return JsonResponse({'suggestions': formatted_suggestions})
            
        except Exception as e:
            return JsonResponse({
                'error': 'Error al obtener sugerencias',
                'details': str(e)
            }, status=500)


class KeywordExtractView(View):
    """API para extracción de palabras clave del contenido."""
    
    @method_decorator(login_required)
    @method_decorator(api_rate_limit)
    def post(self, request):
        try:
            data = json.loads(request.body)
            title = data.get('title', '')
            content = data.get('content', '')
            
            if not title and not content:
                return JsonResponse({
                    'error': 'Se requiere título o contenido'
                }, status=400)
            
            # Extraer palabras clave
            extractor = KeywordExtractor()
            keywords = extractor.extract_from_content(title, content)
            
            # Convertir a sugerencias de tags
            keyword_texts = [kw['keyword'] for kw in keywords[:10]]
            suggested_tags = extractor.suggest_tags_from_keywords(keyword_texts)
            
            # Formatear respuesta
            suggestions = []
            for i, keyword in enumerate(keywords[:10]):
                suggestions.append({
                    'keyword': keyword['keyword'],
                    'score': keyword['score'],
                    'frequency': keyword['frequency'],
                    'in_title': keyword['in_title'],
                    'is_tech': keyword['is_tech'],
                    'suggested_tag': suggested_tags[i] if i < len(suggested_tags) else keyword['keyword']
                })
            
            return JsonResponse({
                'suggestions': suggestions,
                'suggested_tags': suggested_tags
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': 'Error al extraer palabras clave',
                'details': str(e)
            }, status=500)


class RelatedTagsView(View):
    """API para obtener tags relacionados."""
    
    @method_decorator(api_rate_limit)
    def get(self, request):
        tags_param = request.GET.get('tags', '')
        limit = min(int(request.GET.get('limit', 5)), 10)
        
        if not tags_param:
            return JsonResponse({'related_tags': []})
        
        try:
            # Parsear tags
            tag_names = [tag.strip() for tag in tags_param.split(',') if tag.strip()]
            
            if not tag_names:
                return JsonResponse({'related_tags': []})
            
            # Obtener tags relacionados
            manager = TagManagerService()
            related_tags = manager.suggest_related_tags(tag_names, limit)
            
            return JsonResponse({'related_tags': related_tags})
            
        except Exception as e:
            return JsonResponse({
                'error': 'Error al obtener tags relacionados',
                'details': str(e)
            }, status=500)


class PopularTagsView(View):
    """API para obtener tags populares."""
    
    @method_decorator(api_rate_limit)
    def get(self, request):
        limit = min(int(request.GET.get('limit', 20)), 50)
        category = request.GET.get('category', '')
        
        # Intentar obtener desde caché
        cache_key = f'popular_tags:{limit}:{category}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'tags': cached_result})
        
        try:
            # Obtener tags populares
            if category:
                popular_tags = TagMetadata.optimized.by_category(category).popular(limit)
            else:
                popular_tags = TagMetadata.optimized.popular(limit)
            
            # Formatear respuesta
            formatted_tags = []
            for metadata in popular_tags:
                formatted_tags.append({
                    'name': metadata.tag.name,
                    'usage_count': metadata.usage_count,
                    'is_trending': metadata.is_trending,
                    'category': metadata.category,
                })
            
            # Guardar en caché por 1 hora
            cache.set(cache_key, formatted_tags, 3600)
            
            return JsonResponse({'tags': formatted_tags})
            
        except Exception as e:
            return JsonResponse({
                'error': 'Error al obtener tags populares',
                'details': str(e)
            }, status=500)


class TrendingTagsView(View):
    """API para obtener tags en tendencia."""
    
    @method_decorator(api_rate_limit)
    def get(self, request):
        limit = min(int(request.GET.get('limit', 10)), 20)
        days = min(int(request.GET.get('days', 7)), 30)
        
        # Intentar obtener desde caché
        cache_key = f'trending_tags:{limit}:{days}'
        cached_result = cache.get(cache_key)
        if cached_result:
            return JsonResponse({'tags': cached_result})
        
        try:
            # Obtener tags trending
            trending_tags = TagMetadata.optimized.trending().order_by('-trending_score')[:limit]
            
            # Formatear respuesta
            formatted_tags = []
            for metadata in trending_tags:
                formatted_tags.append({
                    'name': metadata.tag.name,
                    'usage_count': metadata.usage_count,
                    'trending_score': metadata.trending_score,
                    'category': metadata.category,
                })
            
            # Guardar en caché por 30 minutos
            cache.set(cache_key, formatted_tags, 1800)
            
            return JsonResponse({'tags': formatted_tags})
            
        except Exception as e:
            return JsonResponse({
                'error': 'Error al obtener tags trending',
                'details': str(e)
            }, status=500)


class TagStatsView(View):
    """API para estadísticas de tags."""
    
    @method_decorator(api_rate_limit)
    def get(self, request):
        try:
            # Estadísticas generales
            total_tags = Tag.objects.count()
            total_metadata = TagMetadata.objects.count()
            trending_count = TagMetadata.objects.filter(is_trending=True).count()
            
            # Tags por categoría
            categories = TagMetadata.objects.exclude(category='').values('category').distinct()
            category_stats = []
            
            for cat in categories:
                category = cat['category']
                count = TagMetadata.objects.filter(category=category).count()
                category_stats.append({
                    'category': category,
                    'count': count
                })
            
            return JsonResponse({
                'total_tags': total_tags,
                'total_with_metadata': total_metadata,
                'trending_count': trending_count,
                'categories': category_stats
            })
            
        except Exception as e:
            return JsonResponse({
                'error': 'Error al obtener estadísticas',
                'details': str(e)
            }, status=500)


class TagValidateView(View):
    """API para validar tags."""
    
    @method_decorator(api_rate_limit)
    def post(self, request):
        try:
            data = json.loads(request.body)
            tag_text = data.get('tag', '').strip()
            
            if not tag_text:
                return JsonResponse({
                    'valid': False,
                    'error': 'Tag vacío'
                })
            
            # Validar con el normalizador
            normalizer = TagNormalizer()
            
            try:
                normalized = normalizer.normalize(tag_text)
                canonical = normalizer.get_canonical_form(normalized)
                
                # Verificar si ya existe
                existing_tag = Tag.objects.filter(name__iexact=canonical).first()
                
                return JsonResponse({
                    'valid': True,
                    'original': tag_text,
                    'normalized': normalized,
                    'canonical': canonical,
                    'exists': existing_tag is not None,
                    'suggestions': normalizer.suggest_alternatives(tag_text) if not existing_tag else []
                })
                
            except Exception as validation_error:
                return JsonResponse({
                    'valid': False,
                    'error': str(validation_error),
                    'suggestions': normalizer.suggest_alternatives(tag_text)
                })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'valid': False,
                'error': 'JSON inválido'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'valid': False,
                'error': 'Error al validar tag',
                'details': str(e)
            }, status=500)