"""
Image selector for choosing existing images from ai_posts folder.
"""

import os
from typing import List, Dict, Optional
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class ImageSelector:
    """
    Utility class for selecting images from the ai_posts folder.
    """
    
    AI_POSTS_FOLDERS = [
        'ai_posts/images/',
        'ai_posts/covers/',
        'post_images/',
    ]
    
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
    
    @classmethod
    def get_available_images(cls, folder: str = None) -> List[Dict]:
        """
        Get list of available images from ai_posts folders.
        
        Args:
            folder: Specific folder to search (optional)
            
        Returns:
            List of image dictionaries with metadata
        """
        images = []
        
        # Determine folders to search
        folders_to_search = [folder] if folder else cls.AI_POSTS_FOLDERS
        
        for search_folder in folders_to_search:
            try:
                if default_storage.exists(search_folder):
                    folder_images = cls._get_images_from_folder(search_folder)
                    images.extend(folder_images)
            except Exception as e:
                logger.warning(f"Error accessing folder {search_folder}: {e}")
                continue
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
        
        return images
    
    @classmethod
    def _get_images_from_folder(cls, folder: str) -> List[Dict]:
        """Get images from a specific folder."""
        images = []
        
        try:
            # List files in the folder
            files = default_storage.listdir(folder)[1]  # [1] gets files, [0] gets subdirs
            
            for filename in files:
                if cls._is_image_file(filename):
                    file_path = os.path.join(folder, filename)
                    image_info = cls._get_image_info(file_path, filename)
                    if image_info:
                        images.append(image_info)
                        
        except Exception as e:
            logger.error(f"Error listing files in folder {folder}: {e}")
        
        return images
    
    @classmethod
    def _is_image_file(cls, filename: str) -> bool:
        """Check if file is a supported image format."""
        return any(filename.lower().endswith(ext) for ext in cls.SUPPORTED_FORMATS)
    
    @classmethod
    def _get_image_info(cls, file_path: str, filename: str) -> Optional[Dict]:
        """Get detailed information about an image file."""
        try:
            # Get file stats
            file_stats = default_storage.get_created_time(file_path)
            file_size = default_storage.size(file_path)
            
            # Get image dimensions
            width, height = cls._get_image_dimensions(file_path)
            
            # Generate thumbnail URL (if needed)
            thumbnail_url = cls._generate_thumbnail_url(file_path)
            
            return {
                'filename': filename,
                'path': file_path,
                'url': default_storage.url(file_path),
                'thumbnail_url': thumbnail_url,
                'size_bytes': file_size,
                'size_mb': round(file_size / (1024 * 1024), 2),
                'width': width,
                'height': height,
                'dimensions': f"{width}x{height}" if width and height else "Unknown",
                'modified_time': file_stats.timestamp() if file_stats else 0,
                'is_suitable_for_cover': cls._is_suitable_for_cover(width, height),
                'folder': os.path.dirname(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error getting info for image {file_path}: {e}")
            return None
    
    @classmethod
    def _get_image_dimensions(cls, file_path: str) -> tuple[Optional[int], Optional[int]]:
        """Get image dimensions."""
        try:
            with default_storage.open(file_path, 'rb') as f:
                with Image.open(f) as img:
                    return img.size
        except Exception as e:
            logger.warning(f"Could not get dimensions for {file_path}: {e}")
            return None, None
    
    @classmethod
    def _generate_thumbnail_url(cls, file_path: str) -> str:
        """Generate thumbnail URL (for now, just return the original URL)."""
        # In the future, this could generate actual thumbnails
        return default_storage.url(file_path)
    
    @classmethod
    def _is_suitable_for_cover(cls, width: Optional[int], height: Optional[int]) -> bool:
        """Check if image dimensions are suitable for cover image."""
        if not width or not height:
            return False
        
        # Check minimum size (300x300 as per our filtering)
        if width < 300 or height < 300:
            return False
        
        # Prefer landscape or square images for covers
        aspect_ratio = width / height
        return 0.5 <= aspect_ratio <= 2.0  # Not too tall or too wide
    
    @classmethod
    def get_images_by_category(cls) -> Dict[str, List[Dict]]:
        """Get images organized by category/folder."""
        categories = {}
        
        for folder in cls.AI_POSTS_FOLDERS:
            folder_name = folder.rstrip('/').split('/')[-1]
            images = cls._get_images_from_folder(folder)
            if images:
                categories[folder_name] = images
        
        return categories
    
    @classmethod
    def search_images(cls, query: str, folder: str = None) -> List[Dict]:
        """
        Search for images by filename or metadata.
        
        Args:
            query: Search query
            folder: Specific folder to search (optional)
            
        Returns:
            List of matching images
        """
        all_images = cls.get_available_images(folder)
        query_lower = query.lower()
        
        matching_images = []
        for image in all_images:
            # Search in filename
            if query_lower in image['filename'].lower():
                matching_images.append(image)
                continue
            
            # Search in folder path
            if query_lower in image['folder'].lower():
                matching_images.append(image)
                continue
        
        return matching_images
    
    @classmethod
    def get_recent_images(cls, limit: int = 20) -> List[Dict]:
        """Get most recently added images."""
        all_images = cls.get_available_images()
        return all_images[:limit]
    
    @classmethod
    def get_suitable_cover_images(cls, limit: int = 50) -> List[Dict]:
        """Get images suitable for use as cover images."""
        all_images = cls.get_available_images()
        suitable_images = [
            img for img in all_images 
            if img['is_suitable_for_cover']
        ]
        return suitable_images[:limit]
    
    @classmethod
    def validate_image_selection(cls, image_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate that an image selection is valid.
        
        Args:
            image_path: Path to the selected image
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not image_path:
            return False, "No image path provided"
        
        # Check if file exists
        if not default_storage.exists(image_path):
            return False, "Selected image file does not exist"
        
        # Check if it's in an allowed folder
        allowed = any(image_path.startswith(folder) for folder in cls.AI_POSTS_FOLDERS)
        if not allowed:
            return False, "Image must be from ai_posts folder"
        
        # Check file format
        if not cls._is_image_file(image_path):
            return False, "File is not a supported image format"
        
        # Check dimensions
        width, height = cls._get_image_dimensions(image_path)
        if not cls._is_suitable_for_cover(width, height):
            return False, f"Image dimensions ({width}x{height}) not suitable for cover"
        
        return True, None
    
    @classmethod
    def get_image_stats(cls) -> Dict:
        """Get statistics about available images."""
        all_images = cls.get_available_images()
        
        if not all_images:
            return {
                'total_images': 0,
                'total_size_mb': 0,
                'suitable_for_cover': 0,
                'by_folder': {}
            }
        
        total_size = sum(img['size_bytes'] for img in all_images)
        suitable_count = sum(1 for img in all_images if img['is_suitable_for_cover'])
        
        # Group by folder
        by_folder = {}
        for img in all_images:
            folder = img['folder']
            if folder not in by_folder:
                by_folder[folder] = 0
            by_folder[folder] += 1
        
        return {
            'total_images': len(all_images),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'suitable_for_cover': suitable_count,
            'by_folder': by_folder
        }