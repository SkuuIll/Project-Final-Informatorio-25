"""
Tests for image selector functionality.
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase
from PIL import Image

from posts.image_generation.image_selector import ImageSelector


class TestImageSelector(TestCase):
    """Test the image selector functionality."""
    
    def setUp(self):
        # Create temporary test images
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test images of different sizes
        self.large_image_path = os.path.join(self.temp_dir, 'large_image.jpg')
        large_img = Image.new('RGB', (1200, 800), color='blue')
        large_img.save(self.large_image_path, 'JPEG')
        
        self.medium_image_path = os.path.join(self.temp_dir, 'medium_image.jpg')
        medium_img = Image.new('RGB', (800, 600), color='green')
        medium_img.save(self.medium_image_path, 'JPEG')
        
        self.small_image_path = os.path.join(self.temp_dir, 'small_image.jpg')
        small_img = Image.new('RGB', (200, 200), color='red')
        small_img.save(self.small_image_path, 'JPEG')
    
    def tearDown(self):
        # Clean up temporary files
        for file_path in [self.large_image_path, self.medium_image_path, self.small_image_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def test_is_image_file_valid_formats(self):
        """Test image file format detection."""
        valid_files = [
            'image.jpg', 'image.jpeg', 'image.png', 
            'image.webp', 'image.gif', 'IMAGE.JPG'
        ]
        
        for filename in valid_files:
            self.assertTrue(ImageSelector._is_image_file(filename))
    
    def test_is_image_file_invalid_formats(self):
        """Test rejection of non-image files."""
        invalid_files = [
            'document.pdf', 'text.txt', 'video.mp4', 
            'archive.zip', 'script.py'
        ]
        
        for filename in invalid_files:
            self.assertFalse(ImageSelector._is_image_file(filename))
    
    def test_is_suitable_for_cover_valid_dimensions(self):
        """Test cover suitability for valid dimensions."""
        valid_dimensions = [
            (800, 600),    # Standard landscape
            (600, 600),    # Square
            (1200, 800),   # Large landscape
            (400, 600),    # Portrait (within ratio)
        ]
        
        for width, height in valid_dimensions:
            self.assertTrue(ImageSelector._is_suitable_for_cover(width, height))
    
    def test_is_suitable_for_cover_invalid_dimensions(self):
        """Test cover suitability for invalid dimensions."""
        invalid_dimensions = [
            (200, 200),    # Too small
            (100, 800),    # Too narrow
            (800, 100),    # Too wide
            (None, 600),   # Missing width
            (800, None),   # Missing height
        ]
        
        for width, height in invalid_dimensions:
            self.assertFalse(ImageSelector._is_suitable_for_cover(width, height))
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_get_available_images_empty_folder(self, mock_storage):
        """Test getting images from empty folder."""
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], [])  # No subdirs, no files
        
        images = ImageSelector.get_available_images('ai_posts/images/')
        
        self.assertEqual(images, [])
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_get_available_images_with_files(self, mock_storage):
        """Test getting images from folder with files."""
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], ['image1.jpg', 'image2.png', 'document.txt'])
        
        # Mock file info
        mock_storage.get_created_time.return_value = MagicMock()
        mock_storage.get_created_time.return_value.timestamp.return_value = 1234567890
        mock_storage.size.return_value = 1024000  # 1MB
        mock_storage.url.return_value = '/media/ai_posts/images/image1.jpg'
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)
            
            images = ImageSelector.get_available_images('ai_posts/images/')
        
        # Should only include image files
        self.assertEqual(len(images), 2)
        
        # Check image info structure
        image_info = images[0]
        self.assertIn('filename', image_info)
        self.assertIn('url', image_info)
        self.assertIn('width', image_info)
        self.assertIn('height', image_info)
        self.assertIn('is_suitable_for_cover', image_info)
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_get_images_by_category(self, mock_storage):
        """Test getting images organized by category."""
        def mock_exists(path):
            return path in ['ai_posts/images/', 'ai_posts/covers/']
        
        def mock_listdir(path):
            if path == 'ai_posts/images/':
                return ([], ['image1.jpg', 'image2.png'])
            elif path == 'ai_posts/covers/':
                return ([], ['cover1.jpg'])
            return ([], [])
        
        mock_storage.exists.side_effect = mock_exists
        mock_storage.listdir.side_effect = mock_listdir
        mock_storage.get_created_time.return_value = MagicMock()
        mock_storage.get_created_time.return_value.timestamp.return_value = 1234567890
        mock_storage.size.return_value = 1024000
        mock_storage.url.return_value = '/media/test.jpg'
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)
            
            categories = ImageSelector.get_images_by_category()
        
        self.assertIn('images', categories)
        self.assertIn('covers', categories)
        self.assertEqual(len(categories['images']), 2)
        self.assertEqual(len(categories['covers']), 1)
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_search_images_by_filename(self, mock_storage):
        """Test searching images by filename."""
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], ['django_tutorial.jpg', 'python_guide.png', 'react_hooks.jpg'])
        mock_storage.get_created_time.return_value = MagicMock()
        mock_storage.get_created_time.return_value.timestamp.return_value = 1234567890
        mock_storage.size.return_value = 1024000
        mock_storage.url.return_value = '/media/test.jpg'
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)
            
            results = ImageSelector.search_images('django')
        
        # Should find the django_tutorial.jpg file
        self.assertEqual(len(results), 1)
        self.assertIn('django_tutorial.jpg', results[0]['filename'])
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_get_suitable_cover_images(self, mock_storage):
        """Test getting only suitable cover images."""
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], ['large.jpg', 'small.jpg'])
        mock_storage.get_created_time.return_value = MagicMock()
        mock_storage.get_created_time.return_value.timestamp.return_value = 1234567890
        mock_storage.size.return_value = 1024000
        mock_storage.url.return_value = '/media/test.jpg'
        
        def mock_dimensions(path):
            if 'large.jpg' in path:
                return (1200, 800)  # Suitable
            elif 'small.jpg' in path:
                return (200, 200)   # Not suitable
            return (800, 600)
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.side_effect = mock_dimensions
            
            suitable_images = ImageSelector.get_suitable_cover_images()
        
        # Should only return the large image
        self.assertEqual(len(suitable_images), 1)
        self.assertIn('large.jpg', suitable_images[0]['filename'])
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_validate_image_selection_valid(self, mock_storage):
        """Test validation of valid image selection."""
        mock_storage.exists.return_value = True
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)
            
            is_valid, error = ImageSelector.validate_image_selection('ai_posts/images/test.jpg')
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_validate_image_selection_nonexistent(self, mock_storage):
        """Test validation of non-existent image."""
        mock_storage.exists.return_value = False
        
        is_valid, error = ImageSelector.validate_image_selection('ai_posts/images/nonexistent.jpg')
        
        self.assertFalse(is_valid)
        self.assertIn('does not exist', error)
    
    def test_validate_image_selection_wrong_folder(self):
        """Test validation of image from wrong folder."""
        is_valid, error = ImageSelector.validate_image_selection('uploads/user_image.jpg')
        
        self.assertFalse(is_valid)
        self.assertIn('ai_posts folder', error)
    
    def test_validate_image_selection_wrong_format(self):
        """Test validation of non-image file."""
        with patch('posts.image_generation.image_selector.default_storage') as mock_storage:
            mock_storage.exists.return_value = True
            
            is_valid, error = ImageSelector.validate_image_selection('ai_posts/images/document.pdf')
        
        self.assertFalse(is_valid)
        self.assertIn('supported image format', error)
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_validate_image_selection_unsuitable_dimensions(self, mock_storage):
        """Test validation of image with unsuitable dimensions."""
        mock_storage.exists.return_value = True
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (100, 100)  # Too small
            
            is_valid, error = ImageSelector.validate_image_selection('ai_posts/images/small.jpg')
        
        self.assertFalse(is_valid)
        self.assertIn('not suitable for cover', error)
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_get_image_stats(self, mock_storage):
        """Test getting image statistics."""
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], ['image1.jpg', 'image2.png'])
        mock_storage.get_created_time.return_value = MagicMock()
        mock_storage.get_created_time.return_value.timestamp.return_value = 1234567890
        mock_storage.size.return_value = 1024000  # 1MB each
        mock_storage.url.return_value = '/media/test.jpg'
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)  # Suitable for cover
            
            stats = ImageSelector.get_image_stats()
        
        self.assertEqual(stats['total_images'], 2)
        self.assertEqual(stats['suitable_for_cover'], 2)
        self.assertGreater(stats['total_size_mb'], 0)
        self.assertIn('by_folder', stats)
    
    @patch('posts.image_generation.image_selector.default_storage')
    def test_get_recent_images_with_limit(self, mock_storage):
        """Test getting recent images with limit."""
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], ['img1.jpg', 'img2.jpg', 'img3.jpg'])
        mock_storage.get_created_time.return_value = MagicMock()
        mock_storage.get_created_time.return_value.timestamp.return_value = 1234567890
        mock_storage.size.return_value = 1024000
        mock_storage.url.return_value = '/media/test.jpg'
        
        with patch.object(ImageSelector, '_get_image_dimensions') as mock_dims:
            mock_dims.return_value = (800, 600)
            
            recent_images = ImageSelector.get_recent_images(limit=2)
        
        # Should respect the limit
        self.assertEqual(len(recent_images), 2)