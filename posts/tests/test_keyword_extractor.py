"""
Tests para el servicio KeywordExtractor.
"""

from django.test import TestCase
from taggit.models import Tag
from posts.services.keyword_extractor import KeywordExtractor


class KeywordExtractorTest(TestCase):
    """Tests para la clase KeywordExtractor."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.extractor = KeywordExtractor()
    
    def test_extract_from_title(self):
        """Test extracción de palabras clave del título."""
        title = "Introducción a Python y Django para Desarrollo Web"
        
        keywords = self.extractor.extract_from_title(title)
        
        # Verificar que se extraigan palabras relevantes
        self.assertIn('python', keywords)
        self.assertIn('django', keywords)
        self.assertIn('desarrollo', keywords)
        self.assertIn('web', keywords)
        
        # Verificar que no se incluyan stop words
        self.assertNotIn('a', keywords)
        self.assertNotIn('para', keywords)
    
    def test_extract_from_content_basic(self):
        """Test extracción básica de contenido."""
        title = "Tutorial de Python"
        content = """
        Python es un lenguaje de programación muy popular.
        Django es un framework web para Python.
        En este tutorial aprenderemos sobre desarrollo web con Python y Django.
        """
        
        keywords = self.extractor.extract_from_content(title, content)
        
        # Verificar que se extraigan palabras técnicas
        python_kw = next((kw for kw in keywords if kw['keyword'] == 'python'), None)
        django_kw = next((kw for kw in keywords if kw['keyword'] == 'django'), None)
        
        self.assertIsNotNone(python_kw)
        self.assertIsNotNone(django_kw)
        
        # Verificar que Python tenga mayor score (está en título)
        self.assertTrue(python_kw['in_title'])
        self.assertFalse(django_kw['in_title'])
        
        # Verificar que se marquen como términos técnicos
        self.assertTrue(python_kw['is_tech'])
        self.assertTrue(django_kw['is_tech'])
    
    def test_extract_from_content_html(self):
        """Test extracción de contenido con HTML."""
        title = "Desarrollo Frontend"
        content = """
        <h2>Introducción a JavaScript</h2>
        <p>JavaScript es un <strong>lenguaje de programación</strong> para el frontend.</p>
        <p>React es una <em>librería</em> muy popular para JavaScript.</p>
        <code>console.log('Hola mundo');</code>
        """
        
        keywords = self.extractor.extract_from_content(title, content)
        
        # Verificar que se extraigan palabras del contenido HTML limpio
        js_kw = next((kw for kw in keywords if kw['keyword'] == 'javascript'), None)
        react_kw = next((kw for kw in keywords if kw['keyword'] == 'react'), None)
        
        self.assertIsNotNone(js_kw)
        self.assertIsNotNone(react_kw)
        
        # Verificar que no se incluyan tags HTML
        html_tags = [kw['keyword'] for kw in keywords if kw['keyword'] in ['h2', 'strong', 'code']]
        self.assertEqual(len(html_tags), 0)
    
    def test_calculate_keyword_score(self):
        """Test cálculo de score de palabras clave."""
        title = "Tutorial de Python"
        content = "Python es genial. Python es fácil de aprender. Programación con Python."
        
        # Calcular score para Python (aparece en título y contenido)
        python_score = self.extractor.calculate_keyword_score('python', title, content)
        
        # Calcular score para programación (solo en contenido)
        prog_score = self.extractor.calculate_keyword_score('programación', title, content)
        
        # Python debería tener mayor score por estar en el título
        self.assertGreater(python_score, prog_score)
        self.assertGreater(python_score, 0.5)  # Score alto por título + frecuencia + tech
    
    def test_filter_relevant_keywords(self):
        """Test filtrado de palabras clave relevantes."""
        keywords = [
            'python',      # Técnico - debería incluirse
            'javascript',  # Técnico - debería incluirse
            'el',          # Stop word - no debería incluirse
            'a',           # Stop word muy corta - no debería incluirse
            'desarrollo',  # Palabra relevante - debería incluirse
            '123',         # Solo números - no debería incluirse
            'ab',          # Muy corta - no debería incluirse
        ]
        
        filtered = self.extractor.filter_relevant_keywords(keywords)
        
        # Verificar inclusiones correctas
        self.assertIn('python', filtered)
        self.assertIn('javascript', filtered)
        self.assertIn('desarrollo', filtered)
        
        # Verificar exclusiones correctas
        self.assertNotIn('el', filtered)
        self.assertNotIn('a', filtered)
        self.assertNotIn('123', filtered)
        self.assertNotIn('ab', filtered)
    
    def test_suggest_tags_from_keywords(self):
        """Test sugerencias de tags desde palabras clave."""
        # Crear algunos tags existentes
        Tag.objects.create(name='python')
        Tag.objects.create(name='web-development')
        
        keywords = ['Python', 'JavaScript', 'web development', 'API']
        
        suggestions = self.extractor.suggest_tags_from_keywords(keywords)
        
        # Verificar que se normalicen correctamente
        self.assertIn('python', suggestions)  # Tag existente
        self.assertIn('javascript', suggestions)  # Nuevo tag normalizado
        self.assertIn('web-development', suggestions)  # Tag existente con guión
        self.assertIn('api', suggestions)  # Normalizado a minúsculas
    
    def test_get_related_tech_terms(self):
        """Test obtención de términos técnicos relacionados."""
        keywords = ['python', 'web']
        
        related = self.extractor.get_related_tech_terms(keywords)
        
        # Verificar que se sugieran términos relacionados con Python
        python_related = ['django', 'flask', 'fastapi', 'pandas', 'numpy']
        web_related = ['html', 'css', 'javascript', 'api', 'rest']
        
        # Al menos algunos términos relacionados deberían estar presentes
        has_python_related = any(term in related for term in python_related)
        has_web_related = any(term in related for term in web_related)
        
        self.assertTrue(has_python_related or has_web_related)
        
        # No debería incluir las keywords originales
        self.assertNotIn('python', related)
        self.assertNotIn('web', related)
    
    def test_clean_text(self):
        """Test limpieza de texto."""
        text = "¡Hola Mundo! ¿Cómo estás? Programación en Python."
        
        cleaned = self.extractor._clean_text(text)
        
        # Verificar que se convierta a minúsculas
        self.assertEqual(cleaned, "hola mundo cómo estás programación en python")
        
        # Test con texto vacío
        self.assertEqual(self.extractor._clean_text(""), "")
        self.assertEqual(self.extractor._clean_text(None), "")
    
    def test_extract_words(self):
        """Test extracción de palabras individuales."""
        text = "python django web-development api rest"
        
        words = self.extractor._extract_words(text)
        
        expected_words = ['python', 'django', 'web', 'development', 'api', 'rest']
        self.assertEqual(words, expected_words)
        
        # Test filtrado por longitud
        text_with_short = "a bb python django"
        words = self.extractor._extract_words(text_with_short)
        
        # Solo palabras de 3+ caracteres
        self.assertNotIn('a', words)
        self.assertNotIn('bb', words)
        self.assertIn('python', words)
        self.assertIn('django', words)
    
    def test_is_valid_keyword(self):
        """Test validación de palabras clave."""
        # Palabras válidas
        self.assertTrue(self.extractor._is_valid_keyword('python'))
        self.assertTrue(self.extractor._is_valid_keyword('javascript'))
        self.assertTrue(self.extractor._is_valid_keyword('desarrollo'))
        
        # Palabras inválidas
        self.assertFalse(self.extractor._is_valid_keyword('el'))  # Stop word
        self.assertFalse(self.extractor._is_valid_keyword('a'))   # Muy corta
        self.assertFalse(self.extractor._is_valid_keyword('123')) # Solo números
        self.assertFalse(self.extractor._is_valid_keyword('ab'))  # Muy corta
        
        # Términos técnicos siempre válidos
        self.assertTrue(self.extractor._is_valid_keyword('api'))
        self.assertTrue(self.extractor._is_valid_keyword('sql'))
    
    def test_calculate_keyword_score_factors(self):
        """Test factores específicos del cálculo de score."""
        # Test bonus por título
        title_score = self.extractor._calculate_keyword_score(
            'python', 1, 10, in_title=True, content_freq=1
        )
        no_title_score = self.extractor._calculate_keyword_score(
            'python', 1, 10, in_title=False, content_freq=1
        )
        
        self.assertGreater(title_score, no_title_score)
        
        # Test bonus por término técnico
        tech_score = self.extractor._calculate_keyword_score(
            'python', 1, 10, in_title=False, content_freq=1
        )
        non_tech_score = self.extractor._calculate_keyword_score(
            'palabra', 1, 10, in_title=False, content_freq=1
        )
        
        self.assertGreater(tech_score, non_tech_score)
    
    def test_extract_with_empty_content(self):
        """Test extracción con contenido vacío."""
        # Solo título
        keywords = self.extractor.extract_from_content("Python Tutorial", "")
        
        self.assertGreater(len(keywords), 0)
        python_kw = next((kw for kw in keywords if kw['keyword'] == 'python'), None)
        self.assertIsNotNone(python_kw)
        self.assertTrue(python_kw['in_title'])
        
        # Título y contenido vacíos
        keywords = self.extractor.extract_from_content("", "")
        self.assertEqual(len(keywords), 0)
    
    def test_extract_with_repeated_words(self):
        """Test extracción con palabras repetidas."""
        title = "Python Python Python"
        content = "Python es genial. Python es fácil. Python es poderoso."
        
        keywords = self.extractor.extract_from_content(title, content)
        
        # Debería haber solo una entrada para Python
        python_keywords = [kw for kw in keywords if kw['keyword'] == 'python']
        self.assertEqual(len(python_keywords), 1)
        
        # Pero con alta frecuencia
        python_kw = python_keywords[0]
        self.assertGreater(python_kw['frequency'], 3)
        self.assertTrue(python_kw['in_title'])
    
    def test_tech_patterns_recognition(self):
        """Test reconocimiento de patrones técnicos."""
        content = "Usamos script.js y styles.css para el frontend. La API REST devuelve JSON."
        
        keywords = self.extractor.extract_from_content("Frontend", content)
        
        # Verificar que se reconozcan patrones técnicos
        keyword_names = [kw['keyword'] for kw in keywords]
        
        # Algunos de estos deberían estar presentes
        tech_terms = ['frontend', 'api', 'rest', 'json', 'script', 'styles']
        found_tech = [term for term in tech_terms if term in keyword_names]
        
        self.assertGreater(len(found_tech), 0)