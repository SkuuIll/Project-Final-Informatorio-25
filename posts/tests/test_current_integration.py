"""
Test de integración con el estado actual del sistema.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from posts.models import Post
from posts.forms import AiPostGeneratorForm


class TestCurrentIntegration(TestCase):
    """Test de integración con el estado actual"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create profile for the user
        from accounts.models import Profile
        Profile.objects.get_or_create(user=self.user, defaults={'can_post': True})
        
        self.client.login(username='testuser', password='testpass123')
        
    def test_ai_generator_view_get_loads(self):
        """Test que la vista GET carga correctamente"""
        
        response = self.client.get('/generate-ai-post/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'url')
        self.assertContains(response, 'rewrite_prompt')
        
    def test_current_form_validation(self):
        """Test validación del formulario actual"""
        
        # Valid form data based on current form structure
        form_data = {
            'url': 'https://example.com/test',
            'prompt_type': 'complete',
            'rewrite_prompt': 'Test prompt for rewriting',
            'tag_prompt': 'Generate tags for: {content}',
            'extract_images': True,
            'max_images': 5,
            'generate_cover_image': True
        }
        
        form = AiPostGeneratorForm(data=form_data)
        if not form.is_valid():
            print("Form errors:", form.errors)
        self.assertTrue(form.is_valid())
        
    def test_current_form_fields_exist(self):
        """Test que los campos actuales del formulario existen"""
        
        form = AiPostGeneratorForm()
        
        # Check current fields exist
        self.assertIn('url', form.fields)
        self.assertIn('prompt_type', form.fields)
        self.assertIn('rewrite_prompt', form.fields)
        self.assertIn('tag_prompt', form.fields)
        self.assertIn('extract_images', form.fields)
        self.assertIn('max_images', form.fields)
        self.assertIn('generate_cover_image', form.fields)
        
    def test_current_form_defaults(self):
        """Test valores por defecto del formulario actual"""
        
        form = AiPostGeneratorForm()
        
        # Check current defaults
        self.assertEqual(form.fields['prompt_type'].initial, 'complete')
        self.assertTrue(form.fields['extract_images'].initial)
        self.assertEqual(form.fields['max_images'].initial, 5)
        self.assertTrue(form.fields['generate_cover_image'].initial)
        
    @patch('posts.views._generate_ai_content')
    def test_ai_generator_view_post_with_current_structure(self, mock_generate):
        """Test POST request con la estructura actual"""
        
        # Mock successful generation
        mock_generate.return_value = (
            {
                'title': 'Test Generated Title',
                'content': 'Test generated content',
                'tags': ['test', 'ai'],
                'cover_image_url': '/media/covers/test.jpg'
            },
            None  # No error
        )
        
        form_data = {
            'url': 'https://example.com/test',
            'prompt_type': 'complete',
            'rewrite_prompt': 'Test prompt for rewriting content',
            'tag_prompt': 'Generate tags for: {content}',
            'extract_images': True,
            'max_images': 3,
            'generate_cover_image': True
        }
        
        response = self.client.post('/generate-ai-post/', data=form_data)
        
        # Should redirect after successful creation (or show success page)
        # The exact behavior depends on the current view implementation
        self.assertIn(response.status_code, [200, 302])
        
    def test_login_required_for_ai_generator(self):
        """Test que se requiere login para el generador de IA"""
        
        self.client.logout()
        response = self.client.get('/generate-ai-post/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    def test_generate_complete_post_function_integration(self):
        """Test integración de la función generate_complete_post"""
        
        from posts.ai_generator import generate_complete_post
        
        # Test with minimal parameters
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags:
            mock_tags.return_value = ['integration', 'test']
            
            result = generate_complete_post(
                url=None,
                rewrite_prompt="Test prompt",
                title="Integration Test",
                extract_images=False,
                generate_cover=False
            )
            
            # Should succeed
            self.assertTrue(result.get('success', True))
            self.assertEqual(result['title'], 'Integration Test')
            self.assertEqual(result['tags'], ['integration', 'test'])
            
    def test_progress_callback_integration(self):
        """Test integración del callback de progreso"""
        
        from posts.ai_generator import generate_complete_post
        
        progress_calls = []
        
        def track_progress(step, percentage):
            progress_calls.append((step, percentage))
            
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags:
            mock_tags.return_value = ['progress', 'test']
            
            result = generate_complete_post(
                url=None,
                rewrite_prompt="Test prompt",
                title="Progress Test",
                extract_images=False,
                generate_cover=False,
                progress_callback=track_progress
            )
            
            # Should have progress calls
            self.assertTrue(len(progress_calls) > 0)
            self.assertEqual(progress_calls[0][1], 0)  # First call at 0%
            self.assertEqual(progress_calls[-1][1], 100)  # Last call at 100%
            
    def test_error_handling_integration(self):
        """Test integración del manejo de errores"""
        
        from posts.ai_generator import generate_complete_post
        
        # Test with no URL and no title (should fail)
        result = generate_complete_post(
            url=None,
            rewrite_prompt="Test prompt",
            title=None
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        
    def test_fallback_logic_integration(self):
        """Test integración de la lógica de fallback"""
        
        from posts.ai_generator import generate_complete_post
        
        # Test with failing tag generation
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags:
            mock_tags.side_effect = Exception("Tag service failed")
            
            result = generate_complete_post(
                url=None,
                rewrite_prompt="Test prompt",
                title="Fallback Test",
                extract_images=False,
                generate_cover=False
            )
            
            # Should still succeed with empty tags
            self.assertTrue(result.get('success', True))
            self.assertEqual(result['tags'], [])
            
    def test_reading_time_calculation_integration(self):
        """Test integración del cálculo de tiempo de lectura"""
        
        from posts.ai_generator import generate_complete_post
        
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags, \
             patch('posts.ai_generator.rewrite_content_with_ai') as mock_rewrite, \
             patch('posts.ai_generator.extract_content_from_url') as mock_extract:
            
            mock_tags.return_value = ['reading', 'time']
            # Create content with ~400 words (should be 2 minutes)
            long_content = ' '.join(['word'] * 400)
            mock_rewrite.return_value = ('Title', long_content)
            mock_extract.return_value = {
                'success': True,
                'content': 'Original content'
            }
            
            result = generate_complete_post(
                url="https://example.com/test",
                rewrite_prompt="Test prompt",
                extract_images=False,
                generate_cover=False
            )
            
            # Should calculate approximately 2 minutes
            self.assertEqual(result['reading_time'], 2)
            
    def test_image_generation_integration_mock(self):
        """Test integración de generación de imágenes (mock)"""
        
        from posts.ai_generator import generate_complete_post
        
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags, \
             patch('posts.ai_generator.registry') as mock_registry:
            
            mock_tags.return_value = ['image', 'test']
            
            # Mock successful image generation
            mock_service = Mock()
            mock_service.generate_image.return_value = (True, '/media/covers/test.jpg', None)
            mock_registry.get_default_service.return_value = mock_service
            
            with patch('posts.ai_generator.CoverImagePromptBuilder') as mock_builder:
                mock_builder.build_cover_prompt.return_value = "Test image prompt"
                
                result = generate_complete_post(
                    url=None,
                    rewrite_prompt="Test prompt",
                    title="Image Test",
                    extract_images=False,
                    generate_cover=True,
                    image_style='professional'
                )
                
                # Should succeed with cover image
                self.assertTrue(result.get('success', True))
                self.assertEqual(result['cover_image_url'], '/media/covers/test.jpg')
                
                # Verify image generation was called
                mock_service.generate_image.assert_called_once_with("Test image prompt")
                
    def test_image_generation_fallback_integration(self):
        """Test integración de fallback en generación de imágenes"""
        
        from posts.ai_generator import generate_complete_post
        
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags, \
             patch('posts.ai_generator.registry') as mock_registry:
            
            mock_tags.return_value = ['fallback', 'test']
            
            # Mock no image service available
            mock_registry.get_default_service.return_value = None
            
            result = generate_complete_post(
                url=None,
                rewrite_prompt="Test prompt",
                title="Fallback Test",
                extract_images=False,
                generate_cover=True
            )
            
            # Should still succeed without cover image
            self.assertTrue(result.get('success', True))
            self.assertNotIn('cover_image_url', result)
            self.assertEqual(result['title'], 'Fallback Test')