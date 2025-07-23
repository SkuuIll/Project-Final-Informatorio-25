"""
Tests for specific image generation services.
"""

import os
from unittest.mock import patch, MagicMock
from django.test import TestCase

from posts.image_generation import (
    GeminiImageGenerator,
    OpenAIImageGenerator,
    ImageGenerationServiceRegistry,
    registry
)


class TestGeminiImageGenerator(TestCase):
    """Test Gemini image generation service."""
    
    def setUp(self):
        self.config = {
            'api_key': 'test-api-key',
            'model': 'gemini-1.5-flash'
        }
    
    @patch('posts.image_generation.gemini_generator.genai')
    def test_setup_service_success(self, mock_genai):
        """Test successful service setup."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        service = GeminiImageGenerator(self.config)
        
        self.assertTrue(service.is_available())
        self.assertEqual(service.get_service_name(), "Google Gemini")
        mock_genai.configure.assert_called_with(api_key='test-api-key')
    
    def test_setup_service_no_api_key(self):
        """Test service setup without API key."""
        with patch.dict(os.environ, {}, clear=True):
            service = GeminiImageGenerator({})
            
            self.assertFalse(service.is_available())
    
    @patch('posts.image_generation.gemini_generator.genai')
    @patch('posts.image_generation.gemini_generator.ImageStorage')
    def test_generate_image_success(self, mock_storage, mock_genai):
        """Test successful image generation."""
        # Setup mocks
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock response with image data
        mock_part = MagicMock()
        mock_part.inline_data.data = b'fake image data'
        mock_response = MagicMock()
        mock_response.parts = [mock_part]
        mock_model.generate_content.return_value = mock_response
        
        mock_storage.save_image_from_content.return_value = '/media/test_image.jpg'
        
        service = GeminiImageGenerator(self.config)
        success, url, error = service.generate_image("test prompt")
        
        self.assertTrue(success)
        self.assertEqual(url, '/media/test_image.jpg')
        self.assertIsNone(error)
    
    @patch('posts.image_generation.gemini_generator.genai')
    def test_generate_image_no_image_data(self, mock_genai):
        """Test image generation with no image data in response."""
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        # Mock response without image data
        mock_response = MagicMock()
        mock_response.parts = []
        mock_model.generate_content.return_value = mock_response
        
        service = GeminiImageGenerator(self.config)
        # Don't allow placeholder generation for this test
        success, url, error = service.generate_image("test prompt", allow_placeholder=False)
        
        self.assertFalse(success)
        self.assertIsNone(url)
        self.assertIsNotNone(error)
    
    def test_get_supported_parameters(self):
        """Test getting supported parameters."""
        service = GeminiImageGenerator(self.config)
        params = service.get_supported_parameters()
        
        self.assertIn('size', params)
        self.assertIn('style', params)
        self.assertIn('model', params)
    
    def test_cost_estimate(self):
        """Test cost estimation."""
        service = GeminiImageGenerator(self.config)
        cost = service.get_cost_estimate()
        
        self.assertEqual(cost, 0.01)
    
    def test_time_estimate(self):
        """Test time estimation."""
        service = GeminiImageGenerator(self.config)
        time_est = service.get_generation_time_estimate()
        
        self.assertEqual(time_est, 15)


class TestOpenAIImageGenerator(TestCase):
    """Test OpenAI image generation service."""
    
    def setUp(self):
        self.config = {
            'api_key': 'test-api-key',
            'model': 'dall-e-3'
        }
    
    @patch('posts.image_generation.openai_generator.OpenAI')
    def test_setup_service_success(self, mock_openai_class):
        """Test successful service setup."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        service = OpenAIImageGenerator(self.config)
        
        self.assertTrue(service.is_available())
        self.assertEqual(service.get_service_name(), "OpenAI DALL-E")
        mock_openai_class.assert_called_with(api_key='test-api-key')
    
    def test_setup_service_no_api_key(self):
        """Test service setup without API key."""
        service = OpenAIImageGenerator({})
        
        self.assertFalse(service.is_available())
    
    @patch('posts.image_generation.openai_generator.OpenAI')
    @patch('posts.image_generation.openai_generator.ImageStorage')
    def test_generate_image_success(self, mock_storage, mock_openai_class):
        """Test successful image generation."""
        # Setup mocks
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock response
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/image.jpg'
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        mock_client.images.generate.return_value = mock_response
        
        mock_storage.save_image_from_url.return_value = '/media/test_image.jpg'
        
        service = OpenAIImageGenerator(self.config)
        success, url, error = service.generate_image("test prompt")
        
        self.assertTrue(success)
        self.assertEqual(url, '/media/test_image.jpg')
        self.assertIsNone(error)
    
    @patch('posts.image_generation.openai_generator.OpenAI')
    def test_generate_image_no_data(self, mock_openai_class):
        """Test image generation with no data in response."""
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        # Mock empty response
        mock_response = MagicMock()
        mock_response.data = []
        mock_client.images.generate.return_value = mock_response
        
        service = OpenAIImageGenerator(self.config)
        success, url, error = service.generate_image("test prompt")
        
        self.assertFalse(success)
        self.assertIsNone(url)
        self.assertIsNotNone(error)
    
    def test_get_supported_parameters_dalle3(self):
        """Test getting supported parameters for DALL-E 3."""
        service = OpenAIImageGenerator(self.config)
        params = service.get_supported_parameters()
        
        self.assertIn('size', params)
        self.assertIn('quality', params)
        self.assertIn('style', params)
        
        # Check DALL-E 3 specific sizes
        self.assertIn('1792x1024', params['size']['options'])
    
    def test_get_supported_parameters_dalle2(self):
        """Test getting supported parameters for DALL-E 2."""
        config = self.config.copy()
        config['model'] = 'dall-e-2'
        service = OpenAIImageGenerator(config)
        params = service.get_supported_parameters()
        
        self.assertIn('size', params)
        self.assertNotIn('quality', params)  # DALL-E 2 doesn't have quality
        self.assertNotIn('style', params)    # DALL-E 2 doesn't have style
    
    def test_cost_estimate_dalle3_standard(self):
        """Test cost estimation for DALL-E 3 standard quality."""
        service = OpenAIImageGenerator(self.config)
        
        # 1024x1024 standard
        cost = service.get_cost_estimate(size='1024x1024', quality='standard')
        self.assertEqual(cost, 0.040)
        
        # 1792x1024 standard
        cost = service.get_cost_estimate(size='1792x1024', quality='standard')
        self.assertEqual(cost, 0.080)
    
    def test_cost_estimate_dalle3_hd(self):
        """Test cost estimation for DALL-E 3 HD quality."""
        service = OpenAIImageGenerator(self.config)
        
        # 1024x1024 HD
        cost = service.get_cost_estimate(size='1024x1024', quality='hd')
        self.assertEqual(cost, 0.080)
        
        # 1792x1024 HD
        cost = service.get_cost_estimate(size='1792x1024', quality='hd')
        self.assertEqual(cost, 0.120)


class TestImageGenerationServiceRegistry(TestCase):
    """Test the service registry."""
    
    def setUp(self):
        # Clear registry for clean tests
        registry.clear_cache()
    
    def test_register_service(self):
        """Test service registration."""
        class MockService(GeminiImageGenerator):
            pass
        
        registry.register_service('mock', MockService)
        
        self.assertIn('mock', registry._services)
        self.assertEqual(registry._services['mock'], MockService)
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'})
    def test_get_service_available(self):
        """Test getting an available service."""
        with patch('posts.image_generation.gemini_generator.genai'):
            service = registry.get_service('gemini')
            self.assertIsNotNone(service)
            self.assertIsInstance(service, GeminiImageGenerator)
    
    def test_get_service_unavailable(self):
        """Test getting an unavailable service."""
        with patch.dict(os.environ, {}, clear=True):
            service = registry.get_service('gemini')
            self.assertIsNone(service)
    
    def test_get_service_not_registered(self):
        """Test getting a non-registered service."""
        service = registry.get_service('nonexistent')
        self.assertIsNone(service)
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'})
    def test_get_available_services(self):
        """Test getting list of available services."""
        with patch('posts.image_generation.gemini_generator.genai'):
            available = registry.get_available_services()
            self.assertIn('gemini', available)
    
    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test-key'})
    def test_get_default_service(self):
        """Test getting default service."""
        with patch('posts.image_generation.gemini_generator.genai'):
            service = registry.get_default_service()
            self.assertIsNotNone(service)
            self.assertIsInstance(service, GeminiImageGenerator)
    
    def test_get_service_info(self):
        """Test getting service information."""
        info = registry.get_service_info()
        
        self.assertIn('gemini', info)
        self.assertIn('openai', info)
        
        # Check structure
        for service_name, service_info in info.items():
            self.assertIn('class', service_info)
            self.assertIn('available', service_info)
            self.assertIn('service_name', service_info)