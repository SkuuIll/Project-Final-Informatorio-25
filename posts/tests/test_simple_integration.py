"""
Test simple para verificar que la integración básica funciona.
"""

from django.test import TestCase
from unittest.mock import patch, Mock
from posts.ai_generator import generate_complete_post


class TestSimpleIntegration(TestCase):
    """Test simple de integración"""
    
    def test_function_exists_and_callable(self):
        """Test que la función existe y es callable"""
        self.assertTrue(callable(generate_complete_post))
        
    def test_function_signature(self):
        """Test que la función tiene la signatura correcta"""
        import inspect
        sig = inspect.signature(generate_complete_post)
        
        # Verify required parameters
        self.assertIn('url', sig.parameters)
        self.assertIn('rewrite_prompt', sig.parameters)
        
        # Verify optional parameters with defaults
        self.assertEqual(sig.parameters['extract_images'].default, True)
        self.assertEqual(sig.parameters['max_images'].default, 5)
        self.assertEqual(sig.parameters['title'].default, None)
        self.assertEqual(sig.parameters['generate_cover'].default, True)
        self.assertEqual(sig.parameters['image_style'].default, 'professional')
        self.assertEqual(sig.parameters['progress_callback'].default, None)
        
    def test_error_when_no_url_and_no_title(self):
        """Test que retorna error cuando no hay URL ni título"""
        result = generate_complete_post(
            url=None,
            rewrite_prompt="Test prompt",
            title=None
        )
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Se requiere una URL o un título', result['error'])
        
    @patch('posts.ai_generator.generate_tags_with_ai')
    def test_basic_functionality_with_title_only(self, mock_tags):
        """Test funcionalidad básica solo con título"""
        mock_tags.return_value = ['test', 'basic']
        
        result = generate_complete_post(
            url=None,
            rewrite_prompt="Test prompt",
            title="Test Title",
            extract_images=False,
            generate_cover=False
        )
        
        # Should succeed
        self.assertTrue(result.get('success', True))
        self.assertEqual(result['title'], 'Test Title')
        self.assertEqual(result['content'], 'Contenido generado automáticamente.')
        self.assertEqual(result['tags'], ['test', 'basic'])
        self.assertEqual(result['reading_time'], 1)
        
    @patch('posts.ai_generator.extract_content_from_url')
    @patch('posts.ai_generator.rewrite_content_with_ai')
    @patch('posts.ai_generator.generate_tags_with_ai')
    def test_basic_functionality_with_url(self, mock_tags, mock_rewrite, mock_extract):
        """Test funcionalidad básica con URL"""
        
        # Setup mocks
        mock_extract.return_value = {
            'success': True,
            'content': 'Test content from URL'
        }
        mock_rewrite.return_value = ('Generated Title', 'Generated content')
        mock_tags.return_value = ['url', 'test']
        
        result = generate_complete_post(
            url="https://example.com/test",
            rewrite_prompt="Test prompt",
            extract_images=False,
            generate_cover=False
        )
        
        # Should succeed
        self.assertTrue(result.get('success', True))
        self.assertEqual(result['title'], 'Generated Title')
        self.assertEqual(result['content'], 'Generated content')
        self.assertEqual(result['tags'], ['url', 'test'])
        
        # Verify functions were called
        mock_extract.assert_called_once_with("https://example.com/test")
        mock_rewrite.assert_called_once()
        mock_tags.assert_called_once()
        
    def test_progress_callback_called(self):
        """Test que el callback de progreso es llamado"""
        progress_calls = []
        
        def mock_progress(step, percentage):
            progress_calls.append((step, percentage))
            
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags:
            mock_tags.return_value = ['progress', 'test']
            
            result = generate_complete_post(
                url=None,
                rewrite_prompt="Test prompt",
                title="Test Title",
                extract_images=False,
                generate_cover=False,
                progress_callback=mock_progress
            )
            
            # Should have progress calls
            self.assertTrue(len(progress_calls) > 0)
            self.assertEqual(progress_calls[0][1], 0)  # First call at 0%
            self.assertEqual(progress_calls[-1][1], 100)  # Last call at 100%
            
    @patch('posts.ai_generator.extract_content_from_url')
    def test_content_extraction_failure(self, mock_extract):
        """Test manejo de fallo en extracción de contenido"""
        
        mock_extract.return_value = {
            'success': False,
            'error': 'Failed to extract content'
        }
        
        result = generate_complete_post(
            url="https://invalid-url.com",
            rewrite_prompt="Test prompt"
        )
        
        # Should fail with extraction error
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'Failed to extract content')
        
    @patch('posts.ai_generator.extract_content_from_url')
    @patch('posts.ai_generator.rewrite_content_with_ai')
    @patch('posts.ai_generator.generate_tags_with_ai')
    def test_tag_generation_failure_fallback(self, mock_tags, mock_rewrite, mock_extract):
        """Test fallback cuando falla la generación de tags"""
        
        mock_extract.return_value = {
            'success': True,
            'content': 'Test content'
        }
        mock_rewrite.return_value = ('Title', 'Content')
        mock_tags.side_effect = Exception("Tags service failed")
        
        result = generate_complete_post(
            url="https://example.com/test",
            rewrite_prompt="Test prompt",
            extract_images=False,
            generate_cover=False
        )
        
        # Should still succeed with empty tags
        self.assertTrue(result.get('success', True))
        self.assertEqual(result['tags'], [])
        
    def test_reading_time_calculation(self):
        """Test cálculo de tiempo de lectura"""
        
        with patch('posts.ai_generator.generate_tags_with_ai') as mock_tags:
            mock_tags.return_value = ['reading', 'time']
            
            # Test with different content lengths
            test_cases = [
                ("short content", 1),  # Minimum 1 minute
                (" ".join(["word"] * 200), 1),  # 200 words = 1 minute
                (" ".join(["word"] * 400), 2),  # 400 words = 2 minutes
                (" ".join(["word"] * 600), 3),  # 600 words = 3 minutes
            ]
            
            for content, expected_time in test_cases:
                with self.subTest(content_length=len(content.split())):
                    with patch('posts.ai_generator.rewrite_content_with_ai') as mock_rewrite:
                        mock_rewrite.return_value = ('Title', content)
                        
                        with patch('posts.ai_generator.extract_content_from_url') as mock_extract:
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
                            
                            self.assertEqual(result['reading_time'], expected_time)