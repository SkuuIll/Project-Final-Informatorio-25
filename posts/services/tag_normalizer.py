"""
Servicio de normalización y validación de tags.
Proporciona funcionalidades para normalizar, validar y encontrar tags similares.
"""

import re
import unicodedata
from typing import List, Tuple, Set
from difflib import SequenceMatcher
from django.core.exceptions import ValidationError
from taggit.models import Tag


class TagNormalizer:
    """
    Servicio para normalización y validación de tags.
    """
    
    # Stop words en español que no deberían ser tags
    STOP_WORDS = {
        'el', 'la', 'de', 'en', 'y', 'a', 'que', 'es', 'se', 'no', 'te', 'lo', 'le', 
        'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'un', 
        'una', 'este', 'esta', 'esto', 'ese', 'esa', 'eso', 'aquel', 'aquella', 
        'aquello', 'mi', 'tu', 'su', 'nuestro', 'vuestro', 'mio', 'tuyo', 'suyo',
        'ser', 'estar', 'tener', 'hacer', 'decir', 'poder', 'ir', 'ver', 'dar',
        'saber', 'querer', 'llegar', 'pasar', 'deber', 'poner', 'parecer', 'quedar',
        'haber', 'encontrar', 'seguir', 'venir', 'llevar', 'creer', 'hablar', 'dejar',
        'muy', 'todo', 'también', 'ya', 'otro', 'mucho', 'antes', 'bien', 'donde',
        'más', 'después', 'tanto', 'durante', 'siempre', 'todos', 'solo', 'hasta',
        'sobre', 'también', 'entre', 'sin', 'bajo', 'desde', 'hacia', 'según'
    }
    
    # Configuración de límites
    MAX_LENGTH = 30
    MIN_LENGTH = 2
    
    # Patrones de caracteres permitidos (después de normalización)
    ALLOWED_CHARS_PATTERN = re.compile(r'^[a-z0-9\s\-_\.]+$', re.IGNORECASE)
    SPECIAL_CHARS_REPLACEMENT = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ü': 'u', 'ñ': 'n',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u', 'Ü': 'u', 'Ñ': 'n'
    }
    
    def __init__(self):
        """Inicializa el normalizador."""
        self.similarity_threshold = 0.8
    
    def normalize(self, tag_text: str) -> str:
        """
        Normalización completa de un tag.
        
        Args:
            tag_text: Texto del tag a normalizar
            
        Returns:
            str: Tag normalizado
            
        Raises:
            ValidationError: Si el tag no es válido
        """
        if not tag_text:
            raise ValidationError("El tag no puede estar vacío")
        
        # 1. Convertir a string y limpiar espacios
        normalized = str(tag_text).strip()
        
        # 2. Convertir a minúsculas
        normalized = normalized.lower()
        
        # 3. Normalizar caracteres Unicode
        normalized = self._normalize_unicode(normalized)
        
        # 4. Limpiar caracteres especiales
        normalized = self._clean_special_chars(normalized)
        
        # 5. Normalizar espacios y guiones
        normalized = self._normalize_spaces_and_hyphens(normalized)
        
        # 6. Validar el resultado
        is_valid, error_message = self.is_valid(normalized)
        if not is_valid:
            raise ValidationError(error_message)
        
        return normalized
    
    def is_valid(self, tag_text: str) -> Tuple[bool, str]:
        """
        Validación completa de un tag.
        
        Args:
            tag_text: Texto del tag a validar
            
        Returns:
            Tuple[bool, str]: (es_válido, mensaje_de_error)
        """
        if not tag_text:
            return False, "El tag no puede estar vacío"
        
        # Validar longitud
        if len(tag_text) < self.MIN_LENGTH:
            return False, f"El tag debe tener al menos {self.MIN_LENGTH} caracteres"
        
        if len(tag_text) > self.MAX_LENGTH:
            return False, f"El tag no puede tener más de {self.MAX_LENGTH} caracteres"
        
        # Validar caracteres permitidos
        if not self.ALLOWED_CHARS_PATTERN.match(tag_text):
            return False, "El tag contiene caracteres no permitidos"
        
        # Validar que no sea solo números
        if tag_text.isdigit():
            return False, "El tag no puede ser solo números"
        
        # Validar que no sea una stop word (solo si es de una sola palabra)
        if len(tag_text.split('-')) == 1 and tag_text.lower() in self.STOP_WORDS:
            return False, f"'{tag_text}' es una palabra muy común y no puede ser un tag"
        
        # Validar que no sea solo espacios o guiones
        if re.match(r'^[\s\-_\.]+$', tag_text):
            return False, "El tag no puede contener solo espacios o caracteres especiales"
        
        return True, ""
    
    def find_similar_tags(self, tag_text: str, threshold: float = None) -> List[Tag]:
        """
        Encuentra tags similares usando distancia de Levenshtein.
        
        Args:
            tag_text: Texto del tag a comparar
            threshold: Umbral de similitud (0-1), por defecto usa self.similarity_threshold
            
        Returns:
            List[Tag]: Lista de tags similares ordenados por similitud
        """
        if threshold is None:
            threshold = self.similarity_threshold
        
        normalized_input = self._basic_normalize(tag_text)
        similar_tags = []
        
        # Obtener todos los tags existentes
        existing_tags = Tag.objects.all()
        
        for tag in existing_tags:
            similarity = self._calculate_similarity(normalized_input, tag.name.lower())
            
            if similarity >= threshold:
                similar_tags.append({
                    'tag': tag,
                    'similarity': similarity
                })
        
        # Ordenar por similitud descendente
        similar_tags.sort(key=lambda x: x['similarity'], reverse=True)
        
        return [item['tag'] for item in similar_tags]
    
    def suggest_alternatives(self, tag_text: str) -> List[str]:
        """
        Sugiere alternativas para tags inválidos.
        
        Args:
            tag_text: Texto del tag inválido
            
        Returns:
            List[str]: Lista de sugerencias
        """
        suggestions = []
        
        # Intentar normalizar y ver si se vuelve válido
        try:
            normalized = self.normalize(tag_text)
            suggestions.append(normalized)
        except ValidationError:
            pass
        
        # Buscar tags similares existentes
        similar_tags = self.find_similar_tags(tag_text, threshold=0.6)
        for tag in similar_tags[:3]:  # Máximo 3 sugerencias
            suggestions.append(tag.name)
        
        # Sugerencias basadas en correcciones comunes
        corrected = self._apply_common_corrections(tag_text)
        if corrected and corrected not in suggestions:
            try:
                normalized_corrected = self.normalize(corrected)
                suggestions.append(normalized_corrected)
            except ValidationError:
                pass
        
        return list(set(suggestions))  # Eliminar duplicados
    
    def get_canonical_form(self, tag_text: str) -> str:
        """
        Obtiene la forma canónica de un tag, considerando sinónimos.
        
        Args:
            tag_text: Texto del tag
            
        Returns:
            str: Forma canónica del tag
        """
        from ..models import TagSynonym
        
        normalized = self.normalize(tag_text)
        
        # Buscar si es un sinónimo
        try:
            synonym = TagSynonym.optimized.active().get(synonym_text__iexact=normalized)
            return synonym.main_tag.name
        except TagSynonym.DoesNotExist:
            return normalized
    
    def _normalize_unicode(self, text: str) -> str:
        """Normaliza caracteres Unicode."""
        # Primero reemplazar caracteres acentuados específicos
        for accented, plain in self.SPECIAL_CHARS_REPLACEMENT.items():
            text = text.replace(accented, plain)
        
        # Normalizar forma Unicode y eliminar diacríticos
        text = unicodedata.normalize('NFKD', text)
        text = ''.join(c for c in text if not unicodedata.combining(c))
        
        return text
    
    def _clean_special_chars(self, text: str) -> str:
        """Limpia caracteres especiales no deseados."""
        # Reemplazar múltiples espacios por uno solo
        text = re.sub(r'\s+', ' ', text)
        
        # Reemplazar múltiples guiones por uno solo
        text = re.sub(r'[-_]+', '-', text)
        
        # Eliminar puntos al inicio y final
        text = text.strip('.')
        
        # Eliminar guiones al inicio y final
        text = text.strip('-_')
        
        return text
    
    def _normalize_spaces_and_hyphens(self, text: str) -> str:
        """Normaliza espacios y guiones."""
        # Reemplazar espacios por guiones para tags multi-palabra
        text = text.replace(' ', '-')
        
        # Limpiar guiones múltiples
        text = re.sub(r'-+', '-', text)
        
        # Eliminar guiones al inicio y final
        text = text.strip('-')
        
        return text
    
    def _basic_normalize(self, text: str) -> str:
        """Normalización básica para comparaciones."""
        return self._normalize_unicode(text.lower().strip())
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula similitud entre dos strings usando SequenceMatcher.
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            
        Returns:
            float: Similitud entre 0 y 1
        """
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _apply_common_corrections(self, text: str) -> str:
        """Aplica correcciones comunes a errores de escritura."""
        corrections = {
            # Errores comunes en español
            'programacion': 'programación',
            'inteligencia-artifical': 'inteligencia-artificial',
            'javascrip': 'javascript',
            'phyton': 'python',
            'databse': 'database',
            'machien-learning': 'machine-learning',
            'web-developement': 'web-development',
            'fronted': 'frontend',
            'backed': 'backend',
        }
        
        text_lower = text.lower()
        for error, correction in corrections.items():
            if error in text_lower:
                return text_lower.replace(error, correction)
        
        return text
    
    def batch_normalize(self, tag_texts: List[str]) -> List[Tuple[str, str, bool]]:
        """
        Normaliza múltiples tags en lote.
        
        Args:
            tag_texts: Lista de textos de tags
            
        Returns:
            List[Tuple[str, str, bool]]: Lista de (original, normalizado, es_válido)
        """
        results = []
        
        for tag_text in tag_texts:
            try:
                normalized = self.normalize(tag_text)
                results.append((tag_text, normalized, True))
            except ValidationError:
                results.append((tag_text, tag_text, False))
        
        return results
    
    def detect_duplicates(self, tag_texts: List[str]) -> List[List[str]]:
        """
        Detecta grupos de tags duplicados o muy similares.
        
        Args:
            tag_texts: Lista de textos de tags
            
        Returns:
            List[List[str]]: Lista de grupos de tags similares
        """
        normalized_tags = {}
        
        # Normalizar todos los tags
        for tag_text in tag_texts:
            try:
                normalized = self.normalize(tag_text)
                if normalized not in normalized_tags:
                    normalized_tags[normalized] = []
                normalized_tags[normalized].append(tag_text)
            except ValidationError:
                continue
        
        # Encontrar grupos con más de un elemento
        duplicate_groups = [group for group in normalized_tags.values() if len(group) > 1]
        
        return duplicate_groups