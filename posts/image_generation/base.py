"""
Abstract base class for image generation services.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageGenerationService(ABC):
    """
    Abstract base class for image generation services.
    
    This class defines the interface that all image generation services
    must implement to be compatible with the AI post generation system.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the image generation service.
        
        Args:
            config: Configuration dictionary for the service
        """
        self.config = config or {}
        self._setup_service()
    
    @abstractmethod
    def _setup_service(self) -> None:
        """
        Setup the service with configuration.
        This method should initialize API clients, validate credentials, etc.
        """
        pass
    
    @abstractmethod
    def generate_image(self, prompt: str, **kwargs) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate an image based on the provided prompt.
        
        Args:
            prompt: Text description of the image to generate
            **kwargs: Additional parameters specific to the service
            
        Returns:
            Tuple of (success, image_url_or_path, error_message)
            - success: Boolean indicating if generation was successful
            - image_url_or_path: URL or local path to generated image if successful
            - error_message: Error description if generation failed
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the service is available and properly configured.
        
        Returns:
            True if service is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """
        Get the human-readable name of the service.
        
        Returns:
            Service name string
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """
        Validate the service configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    def get_supported_parameters(self) -> Dict[str, Any]:
        """
        Get the parameters supported by this service.
        
        Returns:
            Dictionary describing supported parameters and their types/defaults
        """
        return {
            'size': {'type': 'string', 'default': '1024x1024', 'description': 'Image dimensions'},
            'quality': {'type': 'string', 'default': 'standard', 'description': 'Image quality'},
            'style': {'type': 'string', 'default': 'natural', 'description': 'Image style'}
        }
    
    def get_cost_estimate(self, **kwargs) -> float:
        """
        Estimate the cost of generating an image with given parameters.
        
        Args:
            **kwargs: Generation parameters
            
        Returns:
            Estimated cost in USD (0.0 if unknown)
        """
        return 0.0
    
    def get_generation_time_estimate(self, **kwargs) -> int:
        """
        Estimate the time required to generate an image.
        
        Args:
            **kwargs: Generation parameters
            
        Returns:
            Estimated time in seconds
        """
        return 30  # Default estimate
    
    def log_generation_attempt(self, prompt: str, success: bool, error: str = None) -> None:
        """
        Log an image generation attempt for monitoring and debugging.
        
        Args:
            prompt: The prompt used for generation
            success: Whether generation was successful
            error: Error message if generation failed
        """
        service_name = self.get_service_name()
        if success:
            logger.info(f"Image generated successfully with {service_name}")
        else:
            logger.error(f"Image generation failed with {service_name}: {error}")


class ImageGenerationError(Exception):
    """Custom exception for image generation errors."""
    
    def __init__(self, message: str, service_name: str = None, error_code: str = None):
        super().__init__(message)
        self.service_name = service_name
        self.error_code = error_code
        
    def __str__(self):
        base_msg = super().__str__()
        if self.service_name:
            base_msg = f"[{self.service_name}] {base_msg}"
        if self.error_code:
            base_msg = f"{base_msg} (Code: {self.error_code})"
        return base_msg


class ServiceUnavailableError(ImageGenerationError):
    """Raised when an image generation service is unavailable."""
    pass


class InvalidConfigurationError(ImageGenerationError):
    """Raised when service configuration is invalid."""
    pass


class APIQuotaExceededError(ImageGenerationError):
    """Raised when API quota or rate limits are exceeded."""
    pass