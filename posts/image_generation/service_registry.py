"""
Service registry for managing image generation services.
"""

from typing import Dict, List, Optional, Type
import logging

from .base import ImageGenerationService
from .config import ImageGenerationConfig

logger = logging.getLogger(__name__)


class ImageGenerationServiceRegistry:
    """
    Registry for managing available image generation services.
    """
    
    _services: Dict[str, Type[ImageGenerationService]] = {}
    _instances: Dict[str, ImageGenerationService] = {}
    
    @classmethod
    def register_service(cls, name: str, service_class: Type[ImageGenerationService]):
        """
        Register an image generation service.
        
        Args:
            name: Service identifier
            service_class: Service class to register
        """
        cls._services[name] = service_class
        logger.info(f"Registered image generation service: {name}")
    
    @classmethod
    def get_service(cls, name: str) -> Optional[ImageGenerationService]:
        """
        Get an instance of a registered service.
        
        Args:
            name: Service identifier
            
        Returns:
            Service instance or None if not available
        """
        if name not in cls._services:
            logger.error(f"Service '{name}' not registered")
            return None
        
        # Return cached instance if available
        if name in cls._instances:
            return cls._instances[name]
        
        try:
            # Create new instance with configuration
            config = ImageGenerationConfig.get_service_config(name)
            service_class = cls._services[name]
            instance = service_class(config)
            
            # Cache instance if it's available
            if instance.is_available():
                cls._instances[name] = instance
                logger.info(f"Created and cached service instance: {name}")
                return instance
            else:
                logger.warning(f"Service '{name}' is not available")
                return None
                
        except Exception as e:
            logger.error(f"Failed to create service instance '{name}': {e}")
            return None
    
    @classmethod
    def get_available_services(cls) -> List[str]:
        """
        Get list of available service names.
        
        Returns:
            List of available service identifiers
        """
        available = []
        for name in cls._services.keys():
            service = cls.get_service(name)
            if service and service.is_available():
                available.append(name)
        return available
    
    @classmethod
    def get_default_service(cls) -> Optional[ImageGenerationService]:
        """
        Get the default image generation service.
        
        Returns:
            Default service instance or None
        """
        config = ImageGenerationConfig.get_config()
        default_name = config.get('default_service', 'gemini')
        
        # Try to get the configured default service
        service = cls.get_service(default_name)
        if service:
            return service
        
        # Fallback to any available service
        available = cls.get_available_services()
        if available:
            fallback_name = available[0]
            logger.info(f"Default service '{default_name}' not available, using fallback: {fallback_name}")
            return cls.get_service(fallback_name)
        
        logger.error("No image generation services available")
        return None
    
    @classmethod
    def get_fallback_services(cls, primary_service: str) -> List[ImageGenerationService]:
        """
        Get fallback services for a primary service.
        
        Args:
            primary_service: Primary service name
            
        Returns:
            List of fallback service instances
        """
        fallback_names = ImageGenerationConfig.get_fallback_services(primary_service)
        fallback_services = []
        
        for name in fallback_names:
            service = cls.get_service(name)
            if service:
                fallback_services.append(service)
        
        return fallback_services
    
    @classmethod
    def clear_cache(cls):
        """Clear cached service instances."""
        cls._instances.clear()
        logger.info("Cleared service instance cache")
    
    @classmethod
    def get_service_info(cls) -> Dict[str, Dict]:
        """
        Get information about all registered services.
        
        Returns:
            Dictionary with service information
        """
        info = {}
        
        for name, service_class in cls._services.items():
            service = cls.get_service(name)
            
            info[name] = {
                'class': service_class.__name__,
                'available': service is not None and service.is_available(),
                'service_name': service.get_service_name() if service else 'Unknown',
            }
            
            if service:
                try:
                    is_valid, error = service.validate_config()
                    info[name]['config_valid'] = is_valid
                    info[name]['config_error'] = error
                    info[name]['supported_parameters'] = service.get_supported_parameters()
                    info[name]['cost_estimate'] = service.get_cost_estimate()
                    info[name]['time_estimate'] = service.get_generation_time_estimate()
                except Exception as e:
                    info[name]['error'] = str(e)
        
        return info


# Global registry instance
registry = ImageGenerationServiceRegistry()


def register_default_services():
    """Register all default image generation services."""
    try:
        from .gemini_generator import GeminiImageGenerator
        registry.register_service('gemini', GeminiImageGenerator)
    except ImportError as e:
        logger.warning(f"Could not register Gemini service: {e}")
    
    try:
        from .openai_generator import OpenAIImageGenerator
        registry.register_service('openai', OpenAIImageGenerator)
    except ImportError as e:
        logger.warning(f"Could not register OpenAI service: {e}")
    
    # Register additional services here as they are implemented
    logger.info("Default image generation services registered")


# Auto-register services when module is imported
register_default_services()