"""
Tests para el servicio TagNormalizer.
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from taggit.models import Tag
from posts.services.tag_normalizer import TagNormalizer
from posts.models import TagSynonym
from django.contrib.auth.models import User


class TagNormalizerTest(TestCase):
    """Tests para la clase TagNormalizer."""
    
    def setUp(self):
        """Configuración inicial para los tests."""
        self.normalizer = TagNormalizer()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_normalize_basic_tag(self):
        """Test normalización básica de tags."""
        # Test conversión a minúsculas
        self.assertEqual(self.normalizer.normalize('PYTHON'), 'python')
        self.assertEqual(self.normalizer.normalize('JavaScript'), 'javascript')
        
        # Test eliminación de espacios extra
        self.assertEqual(self.normalizer.normalize('  django  '), 'django')
        self.assertEqual(self.normalizer.normalize('web development'), 'web-development')
        
        # Test normalización de caracteres especiales
        self.assertEqual(self.normalizer.normalize('programación'), 'programacion')
        self.assertEqual(self.normalizer.normalize('inteligencia artificial'), 'inteligencia-artificial')
    
    def test_normalize_special_characters(self):
        """Test normalización de caracteres especiales."""
        # Acentos
        self.assertEqual(self.normalizer.normalize('análisis'), 'analisis')
        self.assertEqual(self.normalizer.normalize('diseño'), 'diseno')
        
        # Ñ
        self.assertEqual(self.normalizer.normalize('español'), 'espanol')
        
        # Múltiples espacios y guiones
        self.assertEqual(self.normalizer.normalize('machine---learning'), 'machine-learning')
        self.assertEqual(self.normalizer.normalize('web    development'), 'web-development')
        
        # Puntos y guiones al inicio/final
        self.assertEqual(self.normalizer.normalize('.python.'), 'python')
        self.assertEqual(self.normalizer.normalize('-django-'), 'django')
    
    def test_validation_length(self):
        """Test validación de longitud de tags."""
        # Tag muy corto
        is_valid, message = self.normalizer.is_valid('a')
        self.assertFalse(is_valid)
        self.assertIn('al menos 2 caracteres', message)
        
        # Tag muy largo
        long_tag = 'a' * 31
        is_valid, message = self.normalizer.is_valid(long_tag)
        self.assertFalse(is_valid)
        self.assertIn('más de 30 caracteres', message)
        
        # Tag válido
        is_valid, message = self.normalizer.is_valid('python')
        self.assertTrue(is_valid)
        self.assertEqual(message, '')
    
    def test_validation_stop_words(self):
        """Test validación de stop words."""
        # Usar stop words que tengan al menos 2 caracteres
        stop_words = ['que', 'es', 'muy', 'todo', 'son', 'con', 'para', 'del', 'los', 'las']
        
        for word in stop_words:
            is_valid, message = self.normalizer.is_valid(word)
            self.assertFalse(is_valid)
            # Verificar que falle por ser stop word o por longitud
            self.assertTrue('palabra muy común' in message or 'al menos 2 caracteres' in message)
    
    def test_validation_only_numbers(self):
        """Test validación de tags que son solo números."""
        is_valid, message = self.normalizer.is_valid('123')
        self.assertFalse(is_valid)
        self.assertIn('solo números', message)
        
        # Pero números con letras sí son válidos
        is_valid, message = self.normalizer.is_valid('python3')
        self.assertTrue(is_valid)
    
    def test_validation_invalid_characters(self):
        """Test validación de caracteres no permitidos."""
        invalid_tags = ['tag@invalid', 'tag#hash', 'tag$money', 'tag%percent']
        
        for tag in invalid_tags:
            is_valid, message = self.normalizer.is_valid(tag)
            self.assertFalse(is_valid)
            self.assertIn('caracteres no permitidos', message)
    
    def test_validation_only_special_chars(self):
        """Test validación de tags que son solo caracteres especiales."""
        invalid_tags = ['---', '...', '___', '   ']
        
        for tag in invalid_tags:
            is_valid, message = self.normalizer.is_valid(tag)
            self.assertFalse(is_valid)
            self.assertIn('solo espacios o caracteres especiales', message)
    
    def test_find_similar_tags(self):
        """Test búsqueda de tags similares."""
        # Crear algunos tags de prueba
        Tag.objects.create(name='python')
        Tag.objects.create(name='javascript')
        Tag.objects.create(name='java')
        Tag.objects.create(name='django')
        
        # Buscar similares a 'python'
        similar = self.normalizer.find_similar_tags('python', threshold=0.8)
        self.assertIn('python', [tag.name for tag in similar])
        
        # Buscar similares a 'pythn' (con error de tipeo)
        similar = self.normalizer.find_similar_tags('pythn', threshold=0.6)
        python_names = [tag.name for tag in similar]
        self.assertIn('python', python_names)
        
        # Buscar similares a 'java'
        similar = self.normalizer.find_similar_tags('java', threshold=0.6)
        java_names = [tag.name for tag in similar]
        self.assertIn('java', java_names)
        # javascript podría no ser lo suficientemente similar con threshold 0.6
    
    def test_suggest_alternatives(self):
        """Test sugerencias de alternativas."""
        # Crear algunos tags existentes
        Tag.objects.create(name='python')
        Tag.objects.create(name='javascript')
        
        # Sugerencias para tag con error de tipeo
        suggestions = self.normalizer.suggest_alternatives('pythn')
        self.assertIn('python', suggestions)
        
        # Sugerencias para tag con caracteres especiales
        suggestions = self.normalizer.suggest_alternatives('PYTHON!!!')
        self.assertIn('python', suggestions)
        
        # Sugerencias para correcciones comunes
        suggestions = self.normalizer.suggest_alternatives('programacion')
        # Debería sugerir la forma normalizada
        self.assertTrue(len(suggestions) > 0)
    
    def test_get_canonical_form(self):
        """Test obtención de forma canónica con sinónimos."""
        # Crear tag principal y sinónimo
        main_tag = Tag.objects.create(name='javascript')
        TagSynonym.objects.create(
            main_tag=main_tag,
            synonym_text='js',
            created_by=self.user
        )
        
        # Test forma canónica de sinónimo
        canonical = self.normalizer.get_canonical_form('js')
        self.assertEqual(canonical, 'javascript')
        
        # Test forma canónica de tag principal
        canonical = self.normalizer.get_canonical_form('javascript')
        self.assertEqual(canonical, 'javascript')
        
        # Test forma canónica de tag sin sinónimo
        canonical = self.normalizer.get_canonical_form('python')
        self.assertEqual(canonical, 'python')
    
    def test_batch_normalize(self):
        """Test normalización en lote."""
        tags = ['PYTHON', '  Django  ', 'programación', 'invalid@tag', 'js']
        
        results = self.normalizer.batch_normalize(tags)
        
        # Verificar resultados
        self.assertEqual(len(results), 5)
        
        # Python normalizado correctamente
        self.assertEqual(results[0], ('PYTHON', 'python', True))
        
        # Django normalizado correctamente
        self.assertEqual(results[1], ('  Django  ', 'django', True))
        
        # Programación normalizado correctamente
        self.assertEqual(results[2], ('programación', 'programacion', True))
        
        # Tag inválido
        self.assertEqual(results[3][0], 'invalid@tag')
        self.assertFalse(results[3][2])  # No es válido
        
        # JS válido
        self.assertEqual(results[4], ('js', 'js', True))
    
    def test_detect_duplicates(self):
        """Test detección de duplicados."""
        tags = ['Python', 'PYTHON', 'python', 'Django', 'django', 'JavaScript']
        
        duplicates = self.normalizer.detect_duplicates(tags)
        
        # Debería encontrar grupos de duplicados
        self.assertEqual(len(duplicates), 2)  # Python y Django
        
        # Verificar que Python está en un grupo
        python_group = None
        django_group = None
        
        for group in duplicates:
            if 'Python' in group:
                python_group = group
            elif 'Django' in group:
                django_group = group
        
        self.assertIsNotNone(python_group)
        self.assertIsNotNone(django_group)
        self.assertEqual(len(python_group), 3)  # Python, PYTHON, python
        self.assertEqual(len(django_group), 2)  # Django, django
    
    def test_normalize_with_validation_error(self):
        """Test que normalize lance ValidationError para tags inválidos."""
        invalid_tags = ['', 'a', 'el', '123', 'tag@invalid']
        
        for tag in invalid_tags:
            with self.assertRaises(ValidationError):
                self.normalizer.normalize(tag)
    
    def test_similarity_calculation(self):
        """Test cálculo de similitud."""
        # Similitud exacta
        similarity = self.normalizer._calculate_similarity('python', 'python')
        self.assertEqual(similarity, 1.0)
        
        # Similitud parcial
        similarity = self.normalizer._calculate_similarity('python', 'pythn')
        self.assertGreater(similarity, 0.8)
        
        # Sin similitud
        similarity = self.normalizer._calculate_similarity('python', 'javascript')
        self.assertLess(similarity, 0.3)
    
    def test_common_corrections(self):
        """Test correcciones comunes."""
        corrections = {
            'javascrip': 'javascript',
            'phyton': 'python',
            'databse': 'database',
        }
        
        for error, expected in corrections.items():
            corrected = self.normalizer._apply_common_corrections(error)
            self.assertEqual(corrected, expected)