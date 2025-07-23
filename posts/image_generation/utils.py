"""
Utility functions for image processing and storage.
"""

import os
import uuid
import hashlib
from typing import Optional, Tuple
from urllib.parse import urlparse
from PIL import Image, ImageOps
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Utility class for processing and optimizing images."""
    
    # Standard cover image dimensions
    COVER_DIMENSIONS = {
        'large': (1792, 1024),      # OpenAI DALL-E 3 default
        'medium': (1200, 630),      # Social media standard
        'small': (800, 450),        # Blog standard
    }
    
    MAX_FILE_SIZE_MB = 5
    SUPPORTED_FORMATS = ['JPEG', 'PNG', 'WEBP']
    
    @classmethod
    def resize_image(cls, image_path: str, target_size: Tuple[int, int] = None) -> str:
        """
        Resize an image to target dimensions while maintaining aspect ratio.
        
        Args:
            image_path: Path to the image file
            target_size: Target dimensions (width, height). Defaults to medium cover size.
            
        Returns:
            Path to the resized image
        """
        if target_size is None:
            target_size = cls.COVER_DIMENSIONS['medium']
            
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio
                img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
                
                # Generate new filename
                base_name = os.path.splitext(image_path)[0]
                resized_path = f"{base_name}_resized.jpg"
                
                # Save optimized image
                img.save(resized_path, 'JPEG', quality=85, optimize=True)
                
                logger.info(f"Image resized to {target_size}: {resized_path}")
                return resized_path
                
        except Exception as e:
            logger.error(f"Error resizing image {image_path}: {e}")
            return image_path  # Return original if resize fails
    
    @classmethod
    def optimize_image(cls, image_path: str) -> str:
        """
        Optimize an image for web usage (compression, format conversion).
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Path to the optimized image
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Generate optimized filename
                base_name = os.path.splitext(image_path)[0]
                optimized_path = f"{base_name}_optimized.jpg"
                
                # Save with optimization
                img.save(optimized_path, 'JPEG', quality=80, optimize=True)
                
                # Check file size
                file_size_mb = os.path.getsize(optimized_path) / (1024 * 1024)
                if file_size_mb > cls.MAX_FILE_SIZE_MB:
                    # Reduce quality if file is too large
                    quality = max(60, int(80 * (cls.MAX_FILE_SIZE_MB / file_size_mb)))
                    img.save(optimized_path, 'JPEG', quality=quality, optimize=True)
                    logger.info(f"Image quality reduced to {quality} to meet size limit")
                
                logger.info(f"Image optimized: {optimized_path}")
                return optimized_path
                
        except Exception as e:
            logger.error(f"Error optimizing image {image_path}: {e}")
            return image_path  # Return original if optimization fails
    
    @classmethod
    def validate_image(cls, image_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return False, "Image file does not exist"
            
            # Check file size
            file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
            if file_size_mb > cls.MAX_FILE_SIZE_MB:
                return False, f"Image file too large: {file_size_mb:.1f}MB (max: {cls.MAX_FILE_SIZE_MB}MB)"
            
            # Try to open and validate image
            with Image.open(image_path) as img:
                # Check format
                if img.format not in cls.SUPPORTED_FORMATS:
                    return False, f"Unsupported image format: {img.format}"
                
                # Check dimensions (minimum size)
                min_width, min_height = 400, 300
                if img.width < min_width or img.height < min_height:
                    return False, f"Image too small: {img.width}x{img.height} (min: {min_width}x{min_height})"
                
                # Verify image integrity
                img.verify()
                
            return True, None
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"


class ImageStorage:
    """Utility class for storing and managing generated images."""
    
    DEFAULT_FOLDER = 'ai_posts/covers/'
    
    @classmethod
    def generate_unique_filename(cls, original_filename: str = None, prefix: str = 'cover') -> str:
        """
        Generate a unique filename for an image.
        
        Args:
            original_filename: Original filename (optional)
            prefix: Filename prefix
            
        Returns:
            Unique filename
        """
        # Generate UUID-based filename
        unique_id = str(uuid.uuid4())
        
        # Extract extension from original filename if provided
        if original_filename:
            _, ext = os.path.splitext(original_filename)
            if not ext:
                ext = '.jpg'
        else:
            ext = '.jpg'
        
        return f"{prefix}_{unique_id}{ext}"
    
    @classmethod
    def save_image_from_url(cls, image_url: str, folder: str = None) -> Optional[str]:
        """
        Download and save an image from URL.
        
        Args:
            image_url: URL of the image to download
            folder: Storage folder (defaults to DEFAULT_FOLDER)
            
        Returns:
            Local URL of saved image or None if failed
        """
        if folder is None:
            folder = cls.DEFAULT_FOLDER
            
        try:
            # Download image
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Generate unique filename
            parsed_url = urlparse(image_url)
            original_filename = os.path.basename(parsed_url.path)
            filename = cls.generate_unique_filename(original_filename)
            file_path = os.path.join(folder, filename)
            
            # Save file
            file_content = ContentFile(response.content)
            saved_path = default_storage.save(file_path, file_content)
            
            logger.info(f"Image saved from URL: {saved_path}")
            return default_storage.url(saved_path)
            
        except Exception as e:
            logger.error(f"Error saving image from URL {image_url}: {e}")
            return None
    
    @classmethod
    def save_image_from_content(cls, image_content: bytes, filename: str = None, folder: str = None) -> Optional[str]:
        """
        Save image from binary content.
        
        Args:
            image_content: Binary image data
            filename: Desired filename (will be made unique)
            folder: Storage folder (defaults to DEFAULT_FOLDER)
            
        Returns:
            Local URL of saved image or None if failed
        """
        if folder is None:
            folder = cls.DEFAULT_FOLDER
            
        try:
            # Generate unique filename
            if not filename:
                filename = cls.generate_unique_filename()
            else:
                filename = cls.generate_unique_filename(filename)
            
            file_path = os.path.join(folder, filename)
            
            # Save file
            file_content = ContentFile(image_content)
            saved_path = default_storage.save(file_path, file_content)
            
            logger.info(f"Image saved from content: {saved_path}")
            return default_storage.url(saved_path)
            
        except Exception as e:
            logger.error(f"Error saving image from content: {e}")
            return None
    
    @classmethod
    def cleanup_temp_files(cls, file_paths: list) -> None:
        """
        Clean up temporary files.
        
        Args:
            file_paths: List of file paths to delete
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up temp file {file_path}: {e}")
    
    @classmethod
    def get_image_hash(cls, image_path: str) -> Optional[str]:
        """
        Generate a hash for an image file for caching purposes.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            SHA-256 hash of the image or None if failed
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                return hashlib.sha256(image_data).hexdigest()
        except Exception as e:
            logger.error(f"Error generating hash for image {image_path}: {e}")
            return None