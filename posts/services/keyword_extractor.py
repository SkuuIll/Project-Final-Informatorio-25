"""
Servicio de extracción de palabras clave del contenido sin IA.
Analiza título y contenido para extraer términos relevantes para tags.
"""

import re
import math
from typing import List, Dict, Set, Tuple
from collections import Counter, defaultdict
from django.utils.html import strip_tags
from taggit.models import Tag


class KeywordExtractor:
    """
    Extractor de palabras clave del contenido sin dependencias de IA.
    Utiliza análisis de frecuencia, posición y relevancia técnica.
    """
    
    # Stop words en español expandidas
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
        'sobre', 'también', 'entre', 'sin', 'bajo', 'desde', 'hacia', 'según',
        'como', 'cuando', 'donde', 'porque', 'aunque', 'mientras', 'sino', 'pero',
        'sin', 'embargo', 'además', 'entonces', 'ahora', 'aquí', 'allí', 'así',
        'puede', 'pueden', 'podemos', 'podría', 'podrían', 'debe', 'deben', 'debemos',
        'tiene', 'tienen', 'tenemos', 'había', 'habían', 'habíamos', 'habrá', 'habrán',
        'será', 'serán', 'seremos', 'fue', 'fueron', 'fuimos', 'era', 'eran', 'éramos'
    }
    
    # Palabras técnicas comunes que son buenos candidatos para tags
    TECH_KEYWORDS = {
        # Lenguajes de programación
        'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
        'swift', 'kotlin', 'typescript', 'scala', 'perl', 'r', 'matlab', 'sql',
        
        # Frameworks y librerías
        'django', 'flask', 'fastapi', 'react', 'vue', 'angular', 'node', 'express',
        'spring', 'laravel', 'rails', 'asp.net', 'jquery', 'bootstrap', 'tailwind',
        
        # Tecnologías web
        'html', 'css', 'sass', 'less', 'webpack', 'babel', 'npm', 'yarn', 'api',
        'rest', 'graphql', 'json', 'xml', 'ajax', 'cors', 'jwt', 'oauth',
        
        # Bases de datos
        'mysql', 'postgresql', 'mongodb', 'redis', 'sqlite', 'oracle', 'nosql',
        'elasticsearch', 'cassandra', 'dynamodb',
        
        # DevOps y herramientas
        'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'aws', 'azure',
        'gcp', 'terraform', 'ansible', 'nginx', 'apache', 'linux', 'ubuntu',
        
        # Conceptos de programación
        'algoritmo', 'estructura-datos', 'poo', 'funcional', 'async', 'concurrencia',
        'testing', 'tdd', 'bdd', 'refactoring', 'debugging', 'performance',
        
        # IA y Machine Learning
        'machine-learning', 'deep-learning', 'neural-network', 'tensorflow', 'pytorch',
        'scikit-learn', 'pandas', 'numpy', 'data-science', 'big-data', 'analytics',
        
        # Móvil
        'android', 'ios', 'flutter', 'react-native', 'xamarin', 'cordova',
        
        # Otros
        'blockchain', 'cryptocurrency', 'iot', 'cybersecurity', 'cloud', 'microservices',
        'serverless', 'containers', 'virtualization'
    }
    
    # Patrones para identificar términos técnicos
    TECH_PATTERNS = [
        r'\b\w+\.js\b',  # archivos .js
        r'\b\w+\.py\b',  # archivos .py
        r'\b\w+\.html?\b',  # archivos .html
        r'\b\w+\.css\b',  # archivos .css
        r'\bAPI\b',  # API en mayúsculas
        r'\bHTTP[S]?\b',  # HTTP/HTTPS
        r'\bURL\b',  # URL
        r'\bJSON\b',  # JSON
        r'\bXML\b',  # XML
        r'\bSQL\b',  # SQL
    ]
    
    def __init__(self):
        """Inicializa el extractor."""
        self.min_word_length = 3
        self.max_word_length = 30
        self.min_frequency = 2
        
    def extract_from_content(self, title: str, content: str) -> List[Dict]:
        """
        Extrae palabras clave del contenido completo.
        
        Args:
            title: Título del post
            content: Contenido del post (puede incluir HTML)
            
        Returns:
            List[Dict]: Lista de palabras clave con scores y frecuencias
        """
        # Limpiar y preparar texto
        clean_title = self._clean_text(title)
        clean_content = self._clean_text(strip_tags(content))
        
        # Extraer palabras candidatas
        title_words = self._extract_words(clean_title)
        content_words = self._extract_words(clean_content)
        
        # Calcular frecuencias
        title_freq = Counter(title_words)
        content_freq = Counter(content_words)
        total_words = len(content_words)
        
        # Combinar y calcular scores
        all_keywords = {}
        
        # Procesar palabras del título (mayor peso)
        for word, freq in title_freq.items():
            if self._is_valid_keyword(word):
                score = self._calculate_keyword_score(
                    word, freq, total_words, 
                    in_title=True, 
                    content_freq=content_freq.get(word, 0)
                )
                all_keywords[word] = {
                    'keyword': word,
                    'score': score,
                    'frequency': freq + content_freq.get(word, 0),
                    'in_title': True,
                    'is_tech': word.lower() in self.TECH_KEYWORDS
                }
        
        # Procesar palabras del contenido
        for word, freq in content_freq.items():
            if word not in all_keywords and self._is_valid_keyword(word):
                score = self._calculate_keyword_score(
                    word, freq, total_words,
                    in_title=False,
                    content_freq=freq
                )
                all_keywords[word] = {
                    'keyword': word,
                    'score': score,
                    'frequency': freq,
                    'in_title': False,
                    'is_tech': word.lower() in self.TECH_KEYWORDS
                }
        
        # Filtrar y ordenar por score
        filtered_keywords = [
            kw for kw in all_keywords.values() 
            if kw['frequency'] >= self.min_frequency or kw['is_tech'] or kw['in_title']
        ]
        
        # Ordenar por score descendente
        filtered_keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return filtered_keywords[:20]  # Máximo 20 keywords
    
    def extract_from_title(self, title: str) -> List[str]:
        """
        Extrae palabras clave solo del título.
        
        Args:
            title: Título del post
            
        Returns:
            List[str]: Lista de palabras clave del título
        """
        clean_title = self._clean_text(title)
        words = self._extract_words(clean_title)
        
        return [word for word in words if self._is_valid_keyword(word)]
    
    def calculate_keyword_score(self, keyword: str, title: str, content: str) -> float:
        """
        Calcula score de una palabra clave específica.
        
        Args:
            keyword: Palabra clave a evaluar
            title: Título del post
            content: Contenido del post
            
        Returns:
            float: Score de la palabra clave (0-1)
        """
        clean_title = self._clean_text(title)
        clean_content = self._clean_text(strip_tags(content))
        
        title_words = self._extract_words(clean_title)
        content_words = self._extract_words(clean_content)
        
        title_freq = title_words.count(keyword.lower())
        content_freq = content_words.count(keyword.lower())
        total_words = len(content_words)
        
        return self._calculate_keyword_score(
            keyword, content_freq, total_words,
            in_title=title_freq > 0,
            content_freq=content_freq
        )
    
    def filter_relevant_keywords(self, keywords: List[str]) -> List[str]:
        """
        Filtra palabras clave para mantener solo las relevantes.
        
        Args:
            keywords: Lista de palabras clave candidatas
            
        Returns:
            List[str]: Lista filtrada de palabras clave relevantes
        """
        relevant = []
        
        for keyword in keywords:
            if self._is_valid_keyword(keyword):
                # Priorizar términos técnicos
                if keyword.lower() in self.TECH_KEYWORDS:
                    relevant.append(keyword)
                # Incluir si cumple criterios básicos
                elif (len(keyword) >= self.min_word_length and 
                      keyword.lower() not in self.STOP_WORDS):
                    relevant.append(keyword)
        
        return relevant
    
    def suggest_tags_from_keywords(self, keywords: List[str]) -> List[str]:
        """
        Convierte palabras clave en sugerencias de tags.
        
        Args:
            keywords: Lista de palabras clave
            
        Returns:
            List[str]: Lista de tags sugeridos
        """
        from .tag_normalizer import TagNormalizer
        
        normalizer = TagNormalizer()
        suggested_tags = []
        
        for keyword in keywords:
            try:
                # Normalizar la palabra clave
                normalized = normalizer.normalize(keyword)
                
                # Verificar si ya existe como tag
                existing_tags = Tag.objects.filter(name__iexact=normalized)
                if existing_tags.exists():
                    suggested_tags.append(existing_tags.first().name)
                else:
                    suggested_tags.append(normalized)
                    
            except Exception:
                # Si no se puede normalizar, saltar
                continue
        
        return list(set(suggested_tags))  # Eliminar duplicados
    
    def get_related_tech_terms(self, keywords: List[str]) -> List[str]:
        """
        Obtiene términos técnicos relacionados basados en las palabras clave.
        
        Args:
            keywords: Lista de palabras clave encontradas
            
        Returns:
            List[str]: Lista de términos técnicos relacionados
        """
        related_terms = set()
        keywords_lower = [kw.lower() for kw in keywords]
        
        # Mapeo de relaciones técnicas
        tech_relations = {
            'python': ['django', 'flask', 'fastapi', 'pandas', 'numpy'],
            'javascript': ['react', 'vue', 'angular', 'node', 'express'],
            'java': ['spring', 'hibernate', 'maven', 'gradle'],
            'web': ['html', 'css', 'javascript', 'api', 'rest'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'git'],
            'ai': ['machine-learning', 'tensorflow', 'pytorch', 'data-science'],
        }
        
        for keyword in keywords_lower:
            if keyword in tech_relations:
                related_terms.update(tech_relations[keyword])
            
            # Buscar relaciones inversas
            for category, terms in tech_relations.items():
                if keyword in terms:
                    related_terms.add(category)
                    related_terms.update(terms)
        
        # Filtrar términos que ya están en las keywords originales
        related_terms = related_terms - set(keywords_lower)
        
        return list(related_terms)[:5]  # Máximo 5 términos relacionados
    
    def _clean_text(self, text: str) -> str:
        """Limpia y prepara el texto para análisis."""
        if not text:
            return ""
        
        # Convertir a minúsculas
        text = text.lower()
        
        # Reemplazar caracteres especiales con espacios
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _extract_words(self, text: str) -> List[str]:
        """Extrae palabras individuales del texto."""
        if not text:
            return []
        
        # Dividir por espacios y guiones
        words = re.findall(r'\b\w+\b', text)
        
        # Filtrar por longitud
        words = [
            word for word in words 
            if self.min_word_length <= len(word) <= self.max_word_length
        ]
        
        return words
    
    def _is_valid_keyword(self, word: str) -> bool:
        """Determina si una palabra es un candidato válido para keyword."""
        word_lower = word.lower()
        
        # Verificar longitud
        if len(word) < self.min_word_length or len(word) > self.max_word_length:
            return False
        
        # Verificar que no sea stop word
        if word_lower in self.STOP_WORDS:
            return False
        
        # Verificar que no sea solo números
        if word.isdigit():
            return False
        
        # Verificar patrones técnicos
        for pattern in self.TECH_PATTERNS:
            if re.match(pattern, word, re.IGNORECASE):
                return True
        
        # Verificar si es término técnico conocido
        if word_lower in self.TECH_KEYWORDS:
            return True
        
        # Verificar que tenga al menos una letra
        if not re.search(r'[a-zA-Z]', word):
            return False
        
        return True
    
    def _calculate_keyword_score(self, keyword: str, frequency: int, total_words: int, 
                               in_title: bool = False, content_freq: int = 0) -> float:
        """
        Calcula el score de una palabra clave basado en múltiples factores.
        
        Args:
            keyword: La palabra clave
            frequency: Frecuencia en el texto
            total_words: Total de palabras en el contenido
            in_title: Si aparece en el título
            content_freq: Frecuencia en el contenido
            
        Returns:
            float: Score entre 0 y 1
        """
        score = 0.0
        
        # Factor de frecuencia (TF - Term Frequency)
        if total_words > 0:
            tf = frequency / total_words
            score += tf * 0.3
        
        # Bonus por aparecer en el título
        if in_title:
            score += 0.4
        
        # Bonus por ser término técnico
        if keyword.lower() in self.TECH_KEYWORDS:
            score += 0.3
        
        # Bonus por frecuencia absoluta (pero con límite)
        freq_bonus = min(frequency / 10, 0.2)
        score += freq_bonus
        
        # Bonus por longitud apropiada (palabras de 4-8 caracteres son ideales)
        length = len(keyword)
        if 4 <= length <= 8:
            score += 0.1
        elif length > 15:
            score -= 0.1
        
        # Penalización por palabras muy comunes
        if frequency > total_words * 0.05:  # Más del 5% del texto
            score -= 0.1
        
        # Normalizar score entre 0 y 1
        return min(max(score, 0.0), 1.0)
    
    def _load_stop_words(self) -> Set[str]:
        """Carga stop words (ya definidas como constante de clase)."""
        return self.STOP_WORDS
    
    def _load_tech_keywords(self) -> Set[str]:
        """Carga términos técnicos (ya definidos como constante de clase)."""
        return self.TECH_KEYWORDS