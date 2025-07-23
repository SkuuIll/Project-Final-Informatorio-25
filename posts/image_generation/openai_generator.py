"""
OpenAI DALL-E image generation service implementation.
"""

import os
import time
from typing import Tuple, Optional
import logging

from .base import (
    ImageGenerationService, 
    ImageGenerationError, 
    ServiceUnavailableError,
    APIQuotaExceededError,
    InvalidConfigurationError
)
from .utils import ImageStorage

logger = logging.getLogger(__name__)


class OpenAIImageGenerator(ImageGenerationService):
    """
    OpenAI DALL-E image generation service implementation.
    
    Uses OpenAI's DALL-E API to generate images from text prompts.
    """
    
    def __init__(self, config=None):
        self.client = None
        self.api_key = None
        super().__init__(config)
    
    def _setup_service(self):
        """Setup OpenAI service with API key and client."""
        self.api_key = self.config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.model = self.config.get('model', 'dall-e-3')
        
        if not self.api_key:
            logger.warning("OpenAI API key not configured for image generation")
            return
        
        try:
            # Import OpenAI client
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI image generator initialized with model: {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Install with: pip install openai")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
    
    def generate_image(self, prompt: str, **kwargs) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate an image using OpenAI DALL-E.
        
        Args:
            prompt: Text description of the image to generate
            **kwargs: Additional parameters (size, quality, style, etc.)
            
        Returns:
            Tuple of (success, image_url_or_path, error_message)
        """
        if not self.is_available():
            error_msg = "OpenAI service is not available"
            self.log_generation_attempt(prompt, False, error_msg)
            return False, None, error_msg
        
        try:
            # Prepare parameters
            size = kwargs.get('size', '1792x1024')
            quality = kwargs.get('quality', 'standard')
            style = kwargs.get('style', 'natural')
            
            # Build enhanced prompt
            enhanced_prompt = self._build_image_prompt(prompt, **kwargs)
            
            # Generate image
            start_time = time.time()
            response = self.client.images.generate(
                model=self.model,
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            generation_time = time.time() - start_time
            
            # Extract image URL
            if response.data and len(response.data) > 0:
                image_url = response.data[0].url
                
                # Download and save the image locally
                local_url = ImageStorage.save_image_from_url(image_url)
                
                if local_url:
                    logger.info(f"Image generated successfully in {generation_time:.2f}s")
                    self.log_generation_attempt(prompt, True)
                    return True, local_url, None
                else:
                    error_msg = "Failed to save generated image"
                    self.log_generation_attempt(prompt, False, error_msg)
                    return False, None, error_msg
            else:
                error_msg = "No image data in response"
                self.log_generation_attempt(prompt, False, error_msg)
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"Error generating image with OpenAI: {str(e)}"
            logger.error(error_msg)
            self.log_generation_attempt(prompt, False, error_msg)
            
            # Check for specific error types
            error_str = str(e).lower()
            if "quota" in error_str or "rate limit" in error_str:
                raise APIQuotaExceededError(error_msg, "OpenAI")
            elif "invalid" in error_str and "key" in error_str:
                raise InvalidConfigurationError(error_msg, "OpenAI")
            
            return False, None, error_msg
    
    def _build_image_prompt(self, prompt: str, **kwargs) -> str:
        """
        Build an optimized prompt for DALL-E image generation.
        
        Args:
            prompt: Base prompt
            **kwargs: Additional parameters
            
        Returns:
            Enhanced prompt for image generation
        """
        style = kwargs.get('style', 'natural')
        
        # Style enhancements
        style_enhancements = {
            'professional': 'professional, clean, corporate style, high quality',
            'modern': 'modern, minimalist, contemporary design, sleek',
            'tech': 'technological, futuristic, digital, high-tech aesthetic',
            'creative': 'creative, artistic, vibrant, imaginative design',
            'natural': 'natural, realistic, photographic style'
        }
        
        enhancement = style_enhancements.get(style, style_enhancements['natural'])
        
        enhanced_prompt = f"""
        Create a professional blog post cover image about: {prompt}
        
        Style: {enhancement}
        
        The image should be:
        - Suitable for a blog post header/cover
        - Visually appealing and engaging
        - Professional and polished
        - Relevant to the topic
        - High quality and clear
        - Appropriate for web publication
        
        Avoid text overlays or watermarks.
        """.strip()
        
        # Ensure prompt is within DALL-E limits (typically 1000 characters)
        if len(enhanced_prompt) > 1000:
            enhanced_prompt = enhanced_prompt[:997] + "..."
        
        return enhanced_prompt
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and self.api_key is not None
    
    def get_service_name(self) -> str:
        """Get service name."""
        return "OpenAI DALL-E"
    
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate OpenAI configuration."""
        if not self.api_key:
            return False, "OpenAI API key not configured"
        
        if not self.client:
            return False, "OpenAI client not initialized"
        
        try:
            # Test API connection with a simple request
            # Note: This will use a small amount of quota
            test_response = self.client.images.generate(
                model=self.model,
                prompt="test image",
                size="1024x1024",
                n=1
            )
            return True, None
        except Exception as e:
            return False, f"API validation failed: {str(e)}"
    
    def get_supported_parameters(self):
        """Get supported parameters for OpenAI DALL-E."""
        if self.model == 'dall-e-3':
            return {
                'size': {
                    'type': 'string',
                    'default': '1792x1024',
                    'options': ['1024x1024', '1792x1024', '1024x1792'],
                    'description': 'Image dimensions'
                },
                'quality': {
                    'type': 'string',
                    'default': 'standard',
                    'options': ['standard', 'hd'],
                    'description': 'Image quality'
                },
                'style': {
                    'type': 'string',
                    'default': 'natural',
                    'options': ['natural', 'vivid'],
                    'description': 'Image style'
                }
            }
        else:  # dall-e-2
            return {
                'size': {
                    'type': 'string',
                    'default': '1024x1024',
                    'options': ['256x256', '512x512', '1024x1024'],
                    'description': 'Image dimensions'
                }
            }
    
    def get_cost_estimate(self, **kwargs) -> float:
        """Estimate cost for OpenAI image generation."""
        size = kwargs.get('size', '1024x1024')
        quality = kwargs.get('quality', 'standard')
        
        if self.model == 'dall-e-3':
            if quality == 'hd':
                if size == '1024x1024':
                    return 0.080  # $0.080 per image
                else:  # 1792x1024 or 1024x1792
                    return 0.120  # $0.120 per image
            else:  # standard quality
                if size == '1024x1024':
                    return 0.040  # $0.040 per image
                else:  # 1792x1024 or 1024x1792
                    return 0.080  # $0.080 per image
        else:  # dall-e-2
            if size == '1024x1024':
                return 0.020  # $0.020 per image
            elif size == '512x512':
                return 0.018  # $0.018 per image
            else:  # 256x256
                return 0.016  # $0.016 per image
    
    def get_generation_time_estimate(self, **kwargs) -> int:
        """Estimate generation time for OpenAI."""
        quality = kwargs.get('quality', 'standard')
        
        if quality == 'hd':
            return 45  # HD images take longer
        else:
            return 30  # Standard quality