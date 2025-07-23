"""
Tests para la integración de generación de imágenes en el flujo principal de posts.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from posts.ai_generator import generate_complete_post
from posts.models import Post


class TestGenerateCompletePostIntegration(TestCase):
    """Tests para la función generate_complete_post con integración de imágenes"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.test_url = "https://example.com/test-article"
        self.test_prompt = "Reescribe este contenido de manera profesional"
        self.test_title = "Test Article Title"
        
        # Mock progress callback
        self.progress_callback = Mock()
        
    @patch('posts.ai_generator.extract_content_from_url')
    @patch('posts.ai_generator.rewrite_content_with_ai')
    @patch('posts.ai_generator.generate_tags_with_ai')
    def test_basic_post_generation_without_images(self, mock_tags, mock_rewrite, mock_extract):
        """Test generación básica de post sin imágenes"""
        
        # Mock responses
        mock_extract.return_value = {
            'success': True,
            'content': 'Test content from URL'
        }
        mock_rewrite.return_value = ('Generated Title', 'Generated content')
        mock_tags.return_value = ['tag1', 'tag2', 'tag3']
        
        # Call function
        result = generate_complete_post(
            url=self.test_url,
            rewrite_prompt=self.test_prompt,
            extract_images=False,
            generate_cover=False,
            progress_callback=self.progress_callback
        )
        
        # Assertions
        self.assertTrue(result.get('success', True))  # Should not have success=False
        self.assertEqual(result['title'], 'Generated Title')
        self.assertEqual(result['content'], 'Generated content')
        self.assertEqual(result['tags'], ['tag1', 'tag2', 'tag3'])
        self.assertEqual(result['reading_time'], 1)  # Minimum reading time
        
        # Verify progress was reported
        self.progress_callback.assert_called()
        
    @patch('posts.ai_generator.extract_content_from_url')
    @patch('posts.ai_generator.rewrite_content_with_ai')
    @patch('posts.ai_generator.generate_tags_with_ai')
    @patch('posts.ai_generator.extract_images_from_url')
    @patch('posts.ai_generator.download_image')
    def test_post_generation_with_content_images(self, mock_download, mock_extract_images, 
                                               mock_tags, mock_rewrite, mock_extract):
        """Test generación de post con extracción de imágenes del contenido"""
        
        # Mock responses
        mock_extract.return_value = {
            'success': True,
            'content': 'Test content from URL'
        }
        mock_rewrite.return_value = ('Generated Title', 'Generated content')
        mock_tags.return_value = ['tag1', 'tag2']
        mock_extract_images.return_value = [
            {'src': 'https://example.com/image1.jpg', 'alt': 'Image 1'},
            {'src': 'https://example.com/image2.jpg', 'alt': 'Image 2'}
        ]
        mock_download.side_effect = [
            '/media/images/image1.jpg',
            '/media/images/image2.jpg'
        ]
        
        # Call function
        result = generate_complete_post(
            url=self.test_url,
            rewrite_prompt=self.test_prompt,
            extract_images=True,
            max_images=2,
            generate_cover=False
        )
        
        # Assertions
        self.assertTrue(result.get('success', True))
        self.assertEqual(len(result['images']), 2)
        self.assertEqual(result['images'][0]['local_url'], '/media/images/image1.jpg')
        self.assertEqual(result['images'][1]['local_url'], '/media/images/image2.jpg')
        
        # Verify image extraction was called
        mock_extract_images.assert_called_once_with(self.test_url, 2)
        self.assertEqual(mock_download.call_count, 2)
        
    @patch('posts.ai_generator.extract_content_from_url')
    @patch('posts.ai_generator.rewrite_content_with_ai')
    @patch('posts.ai_generator.generate_tags_with_ai')
    def test_post_generation_with_cover_image_success(self, mock_tags, mock_rewrite, mock_extract):
        """Test generación exitosa de imagen de portada"""
        
        # Mock responses
        mock_extract.return_value = {
            'success': True,
            'content': 'Test content from URL'
        }
        mock_rewrite.return_value = ('Generated Title', 'Generated content')
        mock_tags.return_value = ['tech', 'programming']
        
        # Mock image generation modules
        mock_service = Mock()
        mock_service.generate_image.return_value = (True, '/media/covers/generated_image.jpg', None)
        
        mock_registry = Mock()
        mock_registry.get_default_service.return_value = mock_service
        
        mock_prompt_builder = Mock()
        mock_prompt_builder.build_cover_prompt.return_value = "Professional tech blog cover image"
        
        with patch('posts.ai_generator.registry', mock_registry), \
             patch('posts.ai_generator.CoverImagePromptBuilder', mock_prompt_builder):
            
            result = generate_complete_post(
                url=self.test_url,
                rewrite_prompt=self.test_prompt,
                extract_images=False,
                generate_cover=True,
                image_style='professional'
            )
            
            # Assertions
            self.assertTrue(result.get('success', True))
            self.assertEqual(result['cover_image_url'], '/media/covers/generated_image.jpg')
            
            # Verify image generation was called
            mock_registry.get_default_service.assert_called_once()
            mock_service.generate_image.assert_called_once_with("Professional tech blog cover image")
            
    def test_post_generation_without_url_and_title_fails(self):
        """Test que falla cuando no hay URL ni título"""
        
        result = generate_complete_post(
            url=None,
            rewrite_prompt=self.test_prompt,
            title=None
        )
        
        # Should fail
        self.assertFalse(result['success'])
        self.assertIn('error', result)
        self.assertIn('Se requiere una URL o un título', result['error'])
        
    def test_progress_callback_functionality(self):
        """Test que el callback de progreso funciona correctamente"""
        
        progress_calls = []
        
        def mock_progress(step, percentage):
            progress_calls.append((step, percentage))
            
        with patch('posts.ai_generator.extract_content_from_url') as mock_extract, \
             patch('posts.ai_generator.rewrite_content_with_ai') as mock_rewrite, \
             patch('posts.ai_generator.generate_tags_with_ai') as mock_tags:
            
            mock_extract.return_value = {
                'success': True,
                'content': 'Test content'
            }
            mock_rewrite.return_value = ('Title', 'Content')
            mock_tags.return_value = ['test']
            
            result = generate_complete_post(
                url=self.test_url,
                rewrite_prompt=self.test_prompt,
                extract_images=False,
                generate_cover=False,
                progress_callback=mock_progress
            )
            
            # Verify progress was reported
            self.assertTrue(len(progress_calls) > 0)
            
            # Check that progress starts at 0 and ends at 100
            self.assertEqual(progress_calls[0][1], 0)  # First call should be 0%
            self.assertEqual(progress_calls[-1][1], 100)  # Last call should be 100%
            
            # Verify progress is monotonically increasing
            percentages = [call[1] for call in progress_calls]
            self.assertEqual(percentages, sorted(percentages))