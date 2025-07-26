"""
Tests for image generation infrastructure.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase
from PIL import Image

from posts.image_generation import (
    ImageGenerationService,
    ImageProcessor,
    ImageStorage,
    ImageGenerationConfig,
    ImageGenerationError
)


class MockImageGenerationService(ImageGenerationService):
    """Mock implementation for testing."""
    
    def _setup_service(self):
        self.is_configured = True
    
    def generate_image(self, prompt, **kwargs):
        if prompt == "fail":
            return False, None, "Mock failure"
        return True, "http://example.com/image.jpg", None
    
    def is_available(self):
        return self.is_configured
    
    def get_service_name(self):
        return "Mock Service"
    
    def validate_config(self):
        return True, None


class TestImageGenerationService(TestCase):
    """Test the abstract base class and its interface."""
    
    def setUp(self):
        self.service = MockImageGenerationService()
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertTrue(self.service.is_available())
        self.assertEqual(self.service.get_service_name(), "Mock Service")
    
    def test_successful_generation(self):
        """Test successful image generation."""
        success, url, error = self.service.generate_image("test prompt")
        self.assertTrue(success)
        self.assertEqual(url, "http://example.com/image.jpg")
        self.assertIsNone(error)
    
    def test_failed_generation(self):
        """Test failed image generation."""
        success, url, error = self.service.generate_image("fail")
        self.assertFalse(success)
        self.assertIsNone(url)
        self.assertEqual(error, "Mock failure")
    
    def test_supported_parameters(self):
        """Test getting supported parameters."""
        params = self.service.get_supported_parameters()
        self.assertIn('size', params)
        self.assertIn('quality', params)
        self.assertIn('style', params)
    
    def test_cost_estimate(self):
        """Test cost estimation."""
        cost = self.service.get_cost_estimate()
        self.assertEqual(cost, 0.0)
    
    def test_time_estimate(self):
        """Test time estimation."""
        time_est = self.service.get_generation_time_estimate()
        self.assertEqual(time_est, 30)


class TestImageProcessor(TestCase):
    """Test image processing utilities."""
    
    def setUp(self):
        # Create a temporary test image
        self.temp_dir = tempfile.mkdtemp()
        self.test_image_path = os.path.join(self.temp_dir, 'test_image.jpg')
        
        # Create a simple test image
        img = Image.new('RGB', (800, 600), color='red')
        img.save(self.test_image_path, 'JPEG')
    
    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        os.rmdir(self.temp_dir)
    
    def test_resize_image(self):
        """Test image resizing."""
        resized_path = ImageProcessor.resize_image(
            self.test_image_path, 
            target_size=(400, 300)
        )
        
        # Check that resized image exists
        self.assertTrue(os.path.exists(resized_path))
        
        # Check dimensions
        with Image.open(resized_path) as img:
            self.assertEqual(img.size, (400, 300))
        
        # Clean up
        if os.path.exists(resized_path):
            os.remove(resized_path)
    
    def test_optimize_image(self):
        """Test image optimization."""
        optimized_path = ImageProcessor.optimize_image(self.test_image_path)
        
        # Check that optimized image exists
        self.assertTrue(os.path.exists(optimized_path))
        
        # Check that file size is reasonable
        original_size = os.path.getsize(self.test_image_path)
        optimized_size = os.path.getsize(optimized_path)
        
        # Optimized should be smaller or similar size
        self.assertLessEqual(optimized_size, original_size * 1.1)  # Allow 10% margin
        
        # Clean up
        if os.path.exists(optimized_path):
            os.remove(optimized_path)
    
    def test_validate_image_valid(self):
        """Test validation of valid image."""
        is_valid, error = ImageProcessor.validate_image(self.test_image_path)
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_image_nonexistent(self):
        """Test validation of non-existent image."""
        is_valid, error = ImageProcessor.validate_image('/nonexistent/path.jpg')
        self.assertFalse(is_valid)
        self.assertIn('does not exist', error)
    
    def test_validate_image_too_small(self):
        """Test validation of too small image."""
        # Create a very small image
        small_image_path = os.path.join(self.temp_dir, 'small.jpg')
        small_img = Image.new('RGB', (100, 100), color='blue')
        small_img.save(small_image_path, 'JPEG')
        
        is_valid, error = ImageProcessor.validate_image(small_image_path)
        self.assertFalse(is_valid)
        self.assertIn('too small', error)
        
        # Clean up
        os.remove(small_image_path)


class TestImageStorage(TestCase):
    """Test image storage utilities."""
    
    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        filename1 = ImageStorage.generate_unique_filename()
        filename2 = ImageStorage.generate_unique_filename()
        
        # Should be different
        self.assertNotEqual(filename1, filename2)
        
        # Should have correct format
        self.assertTrue(filename1.startswith('cover_'))
        self.assertTrue(filename1.endswith('.jpg'))
    
    def test_generate_unique_filename_with_original(self):
        """Test unique filename generation with original filename."""
        filename = ImageStorage.generate_unique_filename('test.png', 'custom')
        
        self.assertTrue(filename.startswith('custom_'))
        self.assertTrue(filename.endswith('.png'))
    
    @patch('requests.get')
    def test_save_image_from_url_success(self, mock_get):
        """Test saving image from URL."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b'fake image data'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('posts.image_generation.utils.default_storage') as mock_storage:
            mock_storage.save.return_value = 'saved/path/image.jpg'
            mock_storage.url.return_value = '/media/saved/path/image.jpg'
            
            result = ImageStorage.save_image_from_url('http://example.com/image.jpg')
            
            self.assertEqual(result, '/media/saved/path/image.jpg')
            mock_storage.save.assert_called_once()
    
    @patch('requests.get')
    def test_save_image_from_url_failure(self, mock_get):
        """Test saving image from URL with failure."""
        # Mock failed response
        mock_get.side_effect = Exception("Network error")
        
        result = ImageStorage.save_image_from_url('http://example.com/image.jpg')
        self.assertIsNone(result)
    
    def test_cleanup_temp_files(self):
        """Test cleanup of temporary files."""
        # Create temporary files
        temp_files = []
        for i in range(3):
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            temp_files.append(temp_file.name)
        
        # Verify files exist
        for temp_file in temp_files:
            self.assertTrue(os.path.exists(temp_file))
        
        # Clean up
        ImageStorage.cleanup_temp_files(temp_files)
        
        # Verify files are deleted
        for temp_file in temp_files:
            self.assertFalse(os.path.exists(temp_file))


class TestImageGenerationConfig(TestCase):
    """Test configuration management."""
    
    def test_get_config(self):
        """Test getting default configuration."""
        config = ImageGenerationConfig.get_config()
        
        self.assertIn('default_service', config)
        self.assertIn('fallback_enabled', config)
        self.assertIn('max_retries', config)
        self.assertEqual(config['default_service'], 'gemini')
    

    
    @patch.dict(os.environ, {'STABILITY_API_KEY': 'test-key'})
    def test_get_available_services_with_stability(self):
        """Test getting available services with Stability AI configured."""
        services = ImageGenerationConfig.get_available_services()
        self.assertIn('stability', services)
    
    def test_get_available_services_none_configured(self):
        """Test getting available services with none configured."""
        with patch.dict(os.environ, {}, clear=True):
            services = ImageGenerationConfig.get_available_services()
            self.assertEqual(services, [])
    

    
    def test_get_fallback_services(self):
        """Test getting fallback services."""
        with patch.object(ImageGenerationConfig, 'get_available_services') as mock_available:
            mock_available.return_value = ['gemini', 'stability']
            
            fallbacks = ImageGenerationConfig.get_fallback_services('gemini')
            self.assertEqual(fallbacks, ['stability'])
            
            fallbacks = ImageGenerationConfig.get_fallback_services('stability')
            self.assertEqual(fallbacks, ['gemini'])