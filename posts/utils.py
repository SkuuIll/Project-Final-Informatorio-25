"""
Utility functions for safe file operations in the posts app.
"""
import logging
from django.core.files.storage import default_storage
from django.conf import settings

logger = logging.getLogger(__name__)

def safe_get_image_url(file_field):
    """
    Safely get URL from a file field with proper error handling.
    
    Args:
        file_field: Django FileField or ImageField instance
        
    Returns:
        str: URL of the file, or None if not available
    """
    try:
        # Check if file_field is None or empty
        if not file_field:
            logger.debug("File field is None or empty")
            return None
            
        # Check if file_field has a name attribute and it's not empty
        if not hasattr(file_field, 'name') or not file_field.name:
            logger.debug("File field has no name attribute or name is empty")
            return None
            
        # Check if the file actually exists in storage
        if not default_storage.exists(file_field.name):
            logger.warning(f"File does not exist in storage: {file_field.name}")
            return None
            
        # Try to get the URL
        url = file_field.url
        logger.debug(f"Successfully retrieved URL for file: {file_field.name}")
        return url
        
    except ValueError as e:
        # This happens when trying to access .url on a field with no file
        logger.warning(f"ValueError accessing file URL: {e}")
        return None
        
    except AttributeError as e:
        # This happens when file_field doesn't have expected attributes
        logger.warning(f"AttributeError accessing file field: {e}")
        return None
        
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error getting file URL: {e}", exc_info=True)
        return None

def validate_image_file(file_path):
    """
    Validate that an image file exists and is accessible.
    
    Args:
        file_path (str): Path to the image file
        
    Returns:
        dict: Validation result with status and message
    """
    try:
        if not file_path:
            return {
                'valid': False,
                'status': 'empty',
                'message': 'No file path provided'
            }
            
        # Check if file exists in storage
        if not default_storage.exists(file_path):
            logger.warning(f"Image file not found: {file_path}")
            return {
                'valid': False,
                'status': 'not_found',
                'message': f'File not found: {file_path}'
            }
            
        # Try to get file size to verify accessibility
        try:
            size = default_storage.size(file_path)
            if size == 0:
                logger.warning(f"Image file is empty: {file_path}")
                return {
                    'valid': False,
                    'status': 'empty_file',
                    'message': f'File is empty: {file_path}'
                }
        except Exception as e:
            logger.warning(f"Cannot access file size for {file_path}: {e}")
            return {
                'valid': False,
                'status': 'access_error',
                'message': f'Cannot access file: {file_path}'
            }
            
        logger.debug(f"Image file validation successful: {file_path}")
        return {
            'valid': True,
            'status': 'valid',
            'message': 'File is valid and accessible'
        }
        
    except Exception as e:
        logger.error(f"Unexpected error validating image file {file_path}: {e}", exc_info=True)
        return {
            'valid': False,
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }

def get_fallback_image_url():
    """
    Get URL for fallback image when original image is not available.
    
    Returns:
        str: URL of fallback image or None if not available
    """
    try:
        # Try to use a default image from static files
        fallback_paths = [
            'images/no-image-placeholder.png',
            'images/default-post-image.jpg',
            'admin/img/icon-no.svg',  # Django admin default
        ]
        
        for path in fallback_paths:
            if default_storage.exists(path):
                return default_storage.url(path)
                
        # If no fallback image is found, return None
        logger.debug("No fallback image found")
        return None
        
    except Exception as e:
        logger.error(f"Error getting fallback image URL: {e}")
        return None

def safe_file_operation(operation, file_field, *args, **kwargs):
    """
    Safely execute a file operation with comprehensive error handling.
    
    Args:
        operation (callable): The file operation to execute
        file_field: The file field to operate on
        *args, **kwargs: Additional arguments for the operation
        
    Returns:
        tuple: (success: bool, result: any, error: str)
    """
    try:
        if not file_field:
            return False, None, "File field is None or empty"
            
        result = operation(file_field, *args, **kwargs)
        return True, result, None
        
    except ValueError as e:
        error_msg = f"ValueError in file operation: {e}"
        logger.warning(error_msg)
        return False, None, error_msg
        
    except AttributeError as e:
        error_msg = f"AttributeError in file operation: {e}"
        logger.warning(error_msg)
        return False, None, error_msg
        
    except Exception as e:
        error_msg = f"Unexpected error in file operation: {e}"
        logger.error(error_msg, exc_info=True)
        return False, None, error_msg

def log_file_error(context, file_field, error, level='warning'):
    """
    Log file-related errors with appropriate context.
    
    Args:
        context (str): Context where the error occurred
        file_field: The file field that caused the error
        error (Exception or str): The error that occurred
        level (str): Log level ('debug', 'info', 'warning', 'error')
    """
    try:
        # Extract file information safely
        file_info = "unknown"
        if file_field:
            if hasattr(file_field, 'name') and file_field.name:
                file_info = file_field.name
            elif isinstance(file_field, str):
                file_info = file_field
                
        error_msg = f"File error in {context}: {error} (file: {file_info})"
        
        # Log at appropriate level
        log_method = getattr(logger, level, logger.warning)
        log_method(error_msg)
        
    except Exception as e:
        # Fallback logging if even logging fails
        logger.error(f"Error in log_file_error: {e}")