"""
Selector de imágenes para toda la carpeta media.
"""

import os
from typing import List, Dict, Optional
from django.core.files.storage import default_storage
from django.conf import settings
from PIL import Image
import logging

logger = logging.getLogger(__name__)


class MediaImageSelector:
    """
    Utility class for selecting images from the entire media folder.
    """
    
    # Extensiones de imagen soportadas
    SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.svg']
    
    # Carpetas a excluir (pueden contener archivos que no son imágenes o son sensibles)
    EXCLUDED_FOLDERS = [
        '__pycache__',
        '.git',
        '.svn',
        'temp',
        'tmp',
        'cache',
        'logs',
    ]
    
    @classmethod
    def get_all_media_images(cls, folder: str = None) -> List[Dict]:
        """
        Get list of all images from the media folder.
        
        Args:
            folder: Specific folder to search (optional)
            
        Returns:
            List of image dictionaries with metadata
        """
        images = []
        
        # Si se especifica una carpeta, buscar solo en ella
        if folder:
            if default_storage.exists(folder):
                folder_images = cls._get_images_from_folder(folder)
                images.extend(folder_images)
        else:
            # Buscar en toda la carpeta media
            images = cls._scan_media_directory()
        
        # Sort by modification time (newest first)
        images.sort(key=lambda x: x.get('modified_time', 0), reverse=True)
        
        return images
    
    @classmethod
    def _scan_media_directory(cls, base_path: str = '') -> List[Dict]:
        """Escanear recursivamente toda la carpeta media."""
        images = []
        
        try:
            # Obtener el contenido del directorio
            if default_storage.exists(base_path):
                dirs, files = default_storage.listdir(base_path)
                
                # Procesar archivos en el directorio actual
                for filename in files:
                    if cls._is_image_file(filename):
                        file_path = os.path.join(base_path, filename).replace('\\', '/')
                        image_info = cls._get_image_info(file_path, filename)
                        if image_info:
                            images.append(image_info)
                
                # Procesar subdirectorios recursivamente
                for dirname in dirs:
                    if not cls._should_exclude_folder(dirname):
                        subdir_path = os.path.join(base_path, dirname).replace('\\', '/')
                        subdir_images = cls._scan_media_directory(subdir_path)
                        images.extend(subdir_images)
                        
        except Exception as e:
            logger.error(f"Error scanning directory {base_path}: {e}")
        
        return images
    
    @classmethod
    def _get_images_from_folder(cls, folder: str) -> List[Dict]:
        """Get images from a specific folder (non-recursive)."""
        images = []
        
        try:
            # List files in the folder
            files = default_storage.listdir(folder)[1]  # [1] gets files, [0] gets subdirs
            
            for filename in files:
                if cls._is_image_file(filename):
                    file_path = os.path.join(folder, filename).replace('\\', '/')
                    image_info = cls._get_image_info(file_path, filename)
                    if image_info:
                        images.append(image_info)
                        
        except Exception as e:
            logger.error(f"Error listing files in folder {folder}: {e}")
        
        return images
    
    @classmethod
    def _should_exclude_folder(cls, folder_name: str) -> bool:
        """Check if a folder should be excluded from scanning."""
        folder_lower = folder_name.lower()
        return any(excluded in folder_lower for excluded in cls.EXCLUDED_FOLDERS)
    
    @classmethod
    def _is_image_file(cls, filename: str) -> bool:
        """Check if file is a supported image format."""
        return any(filename.lower().endswith(ext) for ext in cls.SUPPORTED_FORMATS)
    
    @classmethod
    def _get_image_info(cls, file_path: str, filename: str) -> Optional[Dict]:
        """Get detailed information about an image file."""
        try:
            # Get file stats
            try:
                file_stats = default_storage.get_created_time(file_path)
                modified_time = file_stats.timestamp() if file_stats else 0
            except:
                modified_time = 0
            
            try:
                file_size = default_storage.size(file_path)
                size_mb = round(file_size / (1024 * 1024), 2)
            except:
                file_size = 0
                size_mb = 0
            
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
                'size_mb': size_mb,
                'width': width,
                'height': height,
                'dimensions': f"{width}x{height}" if width and height else "Unknown",
                'modified_time': modified_time,
                'is_suitable_for_cover': cls._is_suitable_for_cover(width, height),
                'folder': os.path.dirname(file_path),
                'folder_name': os.path.basename(os.path.dirname(file_path)) if os.path.dirname(file_path) else 'root'
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
    def get_folder_structure(cls) -> Dict[str, int]:
        """Get the folder structure with image counts."""
        folder_counts = {}
        images = cls.get_all_media_images()
        
        for image in images:
            folder = image.get('folder', 'root')
            if folder not in folder_counts:
                folder_counts[folder] = 0
            folder_counts[folder] += 1
        
        return dict(sorted(folder_counts.items()))
    
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
        all_images = cls.get_all_media_images(folder)
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
        all_images = cls.get_all_media_images()
        return all_images[:limit]
    
    @classmethod
    def get_suitable_cover_images(cls, limit: int = 50) -> List[Dict]:
        """Get images suitable for use as cover images."""
        all_images = cls.get_all_media_images()
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
        
        # Check file format
        if not cls._is_image_file(image_path):
            return False, "File is not a supported image format"
        
        return True, None
    
    @classmethod
    def get_image_stats(cls) -> Dict:
        """Get statistics about available images."""
        all_images = cls.get_all_media_images()
        
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
    
    @classmethod
    def delete_image(cls, image_path: str) -> tuple[bool, str]:
        """
        Delete an image file with Linux/Ubuntu compatibility.
        
        Args:
            image_path: Path to the image to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Normalizar path para Linux
            image_path = image_path.replace('\\', '/')
            logger.info(f"Attempting to delete image: {image_path}")
            
            if not default_storage.exists(image_path):
                logger.warning(f"Image file does not exist: {image_path}")
                return False, "Image file does not exist"
            
            # Validate it's an image file
            if not cls._is_image_file(image_path):
                logger.warning(f"File is not an image: {image_path}")
                return False, "File is not an image"
            
            # Verificaciones adicionales para Linux/Ubuntu
            try:
                # Obtener ruta completa del archivo
                if hasattr(default_storage, 'path'):
                    full_path = default_storage.path(image_path)
                    logger.info(f"Full file path: {full_path}")
                    
                    # Verificar que el archivo existe en el sistema de archivos
                    if not os.path.exists(full_path):
                        logger.error(f"File does not exist in filesystem: {full_path}")
                        return False, "File does not exist in filesystem"
                    
                    # Verificar permisos de escritura
                    if not os.access(full_path, os.W_OK):
                        logger.error(f"No write permission for file: {full_path}")
                        # Intentar cambiar permisos si es posible
                        try:
                            os.chmod(full_path, 0o666)
                            logger.info(f"Changed file permissions for: {full_path}")
                        except Exception as chmod_error:
                            logger.error(f"Could not change permissions: {chmod_error}")
                            return False, f"No write permission and cannot change permissions: {chmod_error}"
                    
                    # Verificar permisos del directorio padre
                    parent_dir = os.path.dirname(full_path)
                    if not os.access(parent_dir, os.W_OK):
                        logger.error(f"No write permission for directory: {parent_dir}")
                        return False, f"No write permission for directory: {parent_dir}"
                        
            except Exception as path_error:
                logger.warning(f"Could not perform filesystem checks: {path_error}")
            
            # Intentar eliminar el archivo
            try:
                default_storage.delete(image_path)
                logger.info(f"Successfully deleted image: {image_path}")
                
                # Verificar que realmente se eliminó
                if default_storage.exists(image_path):
                    logger.error(f"File still exists after deletion: {image_path}")
                    return False, "File still exists after deletion attempt"
                
                return True, "Image deleted successfully"
                
            except PermissionError as perm_error:
                logger.error(f"Permission error deleting {image_path}: {perm_error}")
                return False, f"Permission denied: {perm_error}"
            except OSError as os_error:
                logger.error(f"OS error deleting {image_path}: {os_error}")
                return False, f"System error: {os_error}"
            
        except Exception as e:
            logger.error(f"Unexpected error deleting image {image_path}: {e}")
            return False, f"Unexpected error: {str(e)}"
    
    @classmethod
    def bulk_delete_images(cls, image_paths: List[str]) -> Dict:
        """
        Delete multiple image files.
        
        Args:
            image_paths: List of paths to images to delete
            
        Returns:
            Dictionary with results
        """
        deleted_count = 0
        errors = []
        
        for image_path in image_paths:
            success, message = cls.delete_image(image_path)
            if success:
                deleted_count += 1
            else:
                errors.append(f"{image_path}: {message}")
        
        return {
            'deleted_count': deleted_count,
            'errors': errors,
            'total_attempted': len(image_paths)
        }