"""
Tests for image filtering by size.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase
from PIL import Image

from posts.ai_generator import download_image, _is_valid_content_image
from posts.image_generation.utils import ImageStorage


class TestImageSizeFiltering(TestCase):
    """Test image size filtering functionality."""
    
    def setUp(self):
        # Create temporary test images of different sizes
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a large image (valid)
        self.large_image_path = os.path.join(self.temp_dir, 'large_image.jpg')
        large_img = Image.new('RGB', (1200, 800), color='blue')
        large_img.save(self.large_image_path, 'JPEG')
        
        # Create a medium image (valid - exactly minimum size)
        self.medium_image_path = os.path.join(self.temp_dir, 'medium_image.jpg')
        medium_img = Image.new('RGB', (300, 300), color='green')
        medium_img.save(self.medium_image_path, 'JPEG')
        
        # Create a small image (invalid)
        self.small_image_path = os.path.join(self.temp_dir, 'small_image.jpg')
        small_img = Image.new('RGB', (250, 250), color='red')
        small_img.save(self.small_image_path, 'JPEG')
        
        # Create a very small image (invalid)
        self.tiny_image_path = os.path.join(self.temp_dir, 'tiny_image.jpg')
        tiny_img = Image.new('RGB', (100, 100), color='yellow')
        tiny_img.save(self.tiny_image_path, 'JPEG')
    
    def tearDown(self):
        # Clean up temporary files
        for file_path in [self.large_image_path, self.medium_image_path, 
                         self.small_image_path, self.tiny_image_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    @patch('requests.get')
    def test_download_image_large_valid(self, mock_get):
        """Test downloading a large valid image."""
        # Mock response with large image
        with open(self.large_image_path, 'rb') as f:
            image_data = f.read()
        
        mock_response = MagicMock()
        mock_response.content = image_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('posts.ai_generator.default_storage') as mock_storage:
            mock_storage.save.return_value = 'saved/large_image.jpg'
            mock_storage.url.return_value = '/media/saved/large_image.jpg'
            mock_storage.exists.return_value = True
            
            result = download_image('http://example.com/large_image.jpg')
            
            # Should succeed
            self.assertEqual(result, '/media/saved/large_image.jpg')
            mock_storage.save.assert_called_once()
    
    @patch('requests.get')
    def test_download_image_medium_valid(self, mock_get):
        """Test downloading a medium valid image (exactly minimum size)."""
        # Mock response with medium image (300x300)
        with open(self.medium_image_path, 'rb') as f:
            image_data = f.read()
        
        mock_response = MagicMock()
        mock_response.content = image_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('posts.ai_generator.default_storage') as mock_storage:
            mock_storage.save.return_value = 'saved/medium_image.jpg'
            mock_storage.url.return_value = '/media/saved/medium_image.jpg'
            mock_storage.exists.return_value = True
            
            result = download_image('http://example.com/medium_image.jpg')
            
            # Should succeed (exactly minimum size)
            self.assertEqual(result, '/media/saved/medium_image.jpg')
            mock_storage.save.assert_called_once()
    
    @patch('requests.get')
    def test_download_image_small_invalid(self, mock_get):
        """Test downloading a small invalid image."""
        # Mock response with small image
        with open(self.small_image_path, 'rb') as f:
            image_data = f.read()
        
        mock_response = MagicMock()
        mock_response.content = image_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = download_image('http://example.com/small_image.jpg')
        
        # Should fail (too small)
        self.assertIsNone(result)
    
    @patch('requests.get')
    def test_download_image_tiny_invalid(self, mock_get):
        """Test downloading a tiny invalid image."""
        # Mock response with tiny image
        with open(self.tiny_image_path, 'rb') as f:
            image_data = f.read()
        
        mock_response = MagicMock()
        mock_response.content = image_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = download_image('http://example.com/tiny_image.jpg')
        
        # Should fail (too small)
        self.assertIsNone(result)
    
    def test_is_valid_content_image_with_size_attributes(self):
        """Test image validation with size attributes in HTML."""
        from bs4 import BeautifulSoup
        
        # Large image (valid)
        large_html = '<img src="test.jpg" width="1000" height="700" alt="test">'
        large_soup = BeautifulSoup(large_html, 'html.parser')
        large_img = large_soup.find('img')
        
        self.assertTrue(_is_valid_content_image(large_img, 'http://example.com'))
        
        # Medium image (valid)
        medium_html = '<img src="test.jpg" width="300" height="300" alt="test">'
        medium_soup = BeautifulSoup(medium_html, 'html.parser')
        medium_img = medium_soup.find('img')
        
        self.assertTrue(_is_valid_content_image(medium_img, 'http://example.com'))
        
        # Small image (invalid)
        small_html = '<img src="test.jpg" width="250" height="250" alt="test">'
        small_soup = BeautifulSoup(small_html, 'html.parser')
        small_img = small_soup.find('img')
        
        self.assertFalse(_is_valid_content_image(small_img, 'http://example.com'))
        
        # Tiny image (invalid)
        tiny_html = '<img src="test.jpg" width="100" height="100" alt="test">'
        tiny_soup = BeautifulSoup(tiny_html, 'html.parser')
        tiny_img = tiny_soup.find('img')
        
        self.assertFalse(_is_valid_content_image(tiny_img, 'http://example.com'))
    
    @patch('requests.get')
    def test_image_storage_save_from_url_with_size_check(self, mock_get):
        """Test ImageStorage.save_image_from_url with size checking."""
        # Mock response with large image
        with open(self.large_image_path, 'rb') as f:
            image_data = f.read()
        
        mock_response = MagicMock()
        mock_response.content = image_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('posts.image_generation.utils.default_storage') as mock_storage:
            mock_storage.save.return_value = 'saved/large_image.jpg'
            mock_storage.url.return_value = '/media/saved/large_image.jpg'
            
            # Test with large image (should succeed)
            result = ImageStorage.save_image_from_url(
                'http://example.com/large_image.jpg',
                min_width=300,
                min_height=300
            )
            
            self.assertEqual(result, '/media/saved/large_image.jpg')
            mock_storage.save.assert_called_once()
    
    @patch('requests.get')
    def test_image_storage_save_from_url_reject_small(self, mock_get):
        """Test ImageStorage.save_image_from_url rejecting small images."""
        # Mock response with small image
        with open(self.small_image_path, 'rb') as f:
            image_data = f.read()
        
        mock_response = MagicMock()
        mock_response.content = image_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test with small image (should fail)
        result = ImageStorage.save_image_from_url(
            'http://example.com/small_image.jpg',
            min_width=300,
            min_height=300
        )
        
        self.assertIsNone(result)
    
    def test_custom_minimum_sizes(self):
        """Test custom minimum sizes."""
        # Test with custom minimum sizes
        with open(self.small_image_path, 'rb') as f:
            image_data = f.read()
        
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = image_data
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            with patch('posts.ai_generator.default_storage') as mock_storage:
                mock_storage.save.return_value = 'saved/small_image.jpg'
                mock_storage.url.return_value = '/media/saved/small_image.jpg'
                mock_storage.exists.return_value = True
                
                # Should succeed with lower minimum requirements
                result = download_image(
                    'http://example.com/small_image.jpg',
                    min_width=200,
                    min_height=200
                )
                
                self.assertEqual(result, '/media/saved/small_image.jpg')
                mock_storage.save.assert_called_once()