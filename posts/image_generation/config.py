"""
Configuration management for image generation services.
"""

import os
from typing import Dict, List, Optional, Any
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class ImageGenerationConfig:
    """Configuration manager for image generation services."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        'default_service': 'gemini',  # Changed to Gemini as default
        'fallback_enabled': True,
        'max_retries': 3,
        'timeout_seconds': 60,
        'default_size': '1024x1024',
        'default_quality': 'standard',
        'default_style': 'professional',
        'cache_enabled': True,
        'cache_duration_hours': 24,
    }
    
    # Service-specific default configurations
    SERVICE_DEFAULTS = {
        'gemini': {
            'model': 'gemini-1.5-flash',
            'size': '1024x1024',
            'style': 'professional',
        },
        'openai': {
            'model': 'dall-e-3',
            'size': '1792x1024',
            'quality': 'standard',
            'style': 'natural',
        },
        'stability': {
            'model': 'stable-diffusion-xl-1024-v1-0',
            'width': 1024,
            'height': 1024,
            'steps': 30,
            'cfg_scale': 7,
        }
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        Get the complete configuration for image generation.
        
        Returns:
            Configuration dictionary
        """
        config = cls.DEFAULT_CONFIG.copy()
        
        # Override with environment variables if present
        env_overrides = {
            'default_service': os.getenv('DEFAULT_IMAGE_SERVICE'),
            'fallback_enabled': cls._get_bool_env('IMAGE_FALLBACK_ENABLED'),
            'max_retries': cls._get_int_env('IMAGE_MAX_RETRIES'),
            'timeout_seconds': cls._get_int_env('IMAGE_TIMEOUT_SECONDS'),
            'default_size': os.getenv('DEFAULT_IMAGE_SIZE'),
            'default_quality': os.getenv('DEFAULT_IMAGE_QUALITY'),
            'cache_enabled': cls._get_bool_env('IMAGE_CACHE_ENABLED'),
            'cache_duration_hours': cls._get_int_env('IMAGE_CACHE_DURATION_HOURS'),
        }
        
        # Apply non-None overrides
        for key, value in env_overrides.items():
            if value is not None:
                config[key] = value
        
        return config
    
    @classmethod
    def get_service_config(cls, service_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific service.
        
        Args:
            service_name: Name of the service ('openai', 'stability', etc.)
            
        Returns:
            Service-specific configuration
        """
        base_config = cls.SERVICE_DEFAULTS.get(service_name, {}).copy()
        
        # Add service-specific environment variables
        if service_name == 'gemini':
            base_config.update({
                'api_key': os.getenv('GOOGLE_API_KEY'),
                'model': os.getenv('GEMINI_MODEL', base_config.get('model')),
            })
        elif service_name == 'openai':
            base_config.update({
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('OPENAI_IMAGE_MODEL', base_config.get('model')),
                'size': os.getenv('OPENAI_IMAGE_SIZE', base_config.get('size')),
                'quality': os.getenv('OPENAI_IMAGE_QUALITY', base_config.get('quality')),
            })
        elif service_name == 'stability':
            base_config.update({
                'api_key': os.getenv('STABILITY_API_KEY'),
                'model': os.getenv('STABILITY_MODEL', base_config.get('model')),
                'width': cls._get_int_env('STABILITY_WIDTH') or base_config.get('width'),
                'height': cls._get_int_env('STABILITY_HEIGHT') or base_config.get('height'),
            })
        
        return base_config
    
    @classmethod
    def get_available_services(cls) -> List[str]:
        """
        Get list of available (configured) image generation services.
        
        Returns:
            List of service names that are properly configured
        """
        available = []
        
        # Check Gemini (Google)
        if os.getenv('GOOGLE_API_KEY'):
            available.append('gemini')
        
        # Check OpenAI
        if os.getenv('OPENAI_API_KEY'):
            available.append('openai')
        
        # Check Stability AI
        if os.getenv('STABILITY_API_KEY'):
            available.append('stability')
        
        return available
    
    @classmethod
    def is_service_available(cls, service_name: str) -> bool:
        """
        Check if a specific service is available.
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            True if service is available, False otherwise
        """
        return service_name in cls.get_available_services()
    
    @classmethod
    def get_fallback_services(cls, primary_service: str) -> List[str]:
        """
        Get list of fallback services for a primary service.
        
        Args:
            primary_service: Primary service name
            
        Returns:
            List of fallback service names
        """
        available = cls.get_available_services()
        
        # Remove primary service from available list
        fallbacks = [s for s in available if s != primary_service]
        
        # Order fallbacks by preference
        preference_order = ['gemini', 'openai', 'stability']
        ordered_fallbacks = []
        
        for preferred in preference_order:
            if preferred in fallbacks:
                ordered_fallbacks.append(preferred)
        
        # Add any remaining services
        for service in fallbacks:
            if service not in ordered_fallbacks:
                ordered_fallbacks.append(service)
        
        return ordered_fallbacks
    
    @classmethod
    def validate_service_config(cls, service_name: str) -> tuple[bool, Optional[str]]:
        """
        Validate configuration for a specific service.
        
        Args:
            service_name: Name of the service to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        config = cls.get_service_config(service_name)
        
        if service_name == 'gemini':
            if not config.get('api_key'):
                return False, "Google API key not configured"
            if not config.get('model'):
                return False, "Gemini model not specified"
                
        elif service_name == 'openai':
            if not config.get('api_key'):
                return False, "OpenAI API key not configured"
            if not config.get('model'):
                return False, "OpenAI model not specified"
                
        elif service_name == 'stability':
            if not config.get('api_key'):
                return False, "Stability AI API key not configured"
            if not config.get('model'):
                return False, "Stability AI model not specified"
                
        else:
            return False, f"Unknown service: {service_name}"
        
        return True, None
    
    @classmethod
    def get_storage_config(cls) -> Dict[str, Any]:
        """
        Get storage-related configuration.
        
        Returns:
            Storage configuration dictionary
        """
        return {
            'cover_image_folder': os.getenv('COVER_IMAGE_FOLDER', 'ai_posts/covers/'),
            'max_image_size_mb': cls._get_int_env('MAX_IMAGE_SIZE_MB') or 5,
            'allowed_formats': ['JPEG', 'PNG', 'WEBP'],
            'default_format': 'JPEG',
            'compression_quality': cls._get_int_env('IMAGE_COMPRESSION_QUALITY') or 85,
        }
    
    @staticmethod
    def _get_bool_env(key: str) -> Optional[bool]:
        """Get boolean value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return None
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @staticmethod
    def _get_int_env(key: str) -> Optional[int]:
        """Get integer value from environment variable."""
        value = os.getenv(key)
        if value is None:
            return None
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Invalid integer value for {key}: {value}")
            return None


# Global configuration instance
config = ImageGenerationConfig()