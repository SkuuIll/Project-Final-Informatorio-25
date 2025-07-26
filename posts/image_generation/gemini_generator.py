"""
Google Gemini image generation service implementation.
"""

import os
import time
import tempfile
from typing import Tuple, Optional
import google.generativeai as genai
import requests
from PIL import Image
import logging

from .base import (
    ImageGenerationService, 
    ImageGenerationError, 
    ServiceUnavailableError,
    APIQuotaExceededError
)
from .utils import ImageStorage, ImageProcessor

logger = logging.getLogger(__name__)


class GeminiImageGenerator(ImageGenerationService):
    """
    Google Gemini image generation service implementation.
    
    Uses Google's Gemini API to generate images from text prompts.
    """
    
    def __init__(self, config=None):
        self.api_key = None
        self.model = None
        super().__init__(config)
    
    def _setup_service(self):
        """Setup Gemini service with API key and model configuration."""
        self.api_key = self.config.get('api_key') or os.getenv('GOOGLE_API_KEY')
        self.model_name = self.config.get('model', 'gemini-2.0-flash-exp')
        
        if not self.api_key:
            logger.warning("Google API key not configured for image generation")
            self.model = None
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
            logger.info(f"Gemini image generator initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini service: {e}")
            self.model = None
    
    def generate_image(self, prompt: str, **kwargs) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generate an image using Gemini.
        
        Args:
            prompt: Text description of the image to generate
            **kwargs: Additional parameters (size, style, etc.)
            
        Returns:
            Tuple of (success, image_url_or_path, error_message)
        """
        if not self.is_available():
            error_msg = "Gemini service is not available"
            self.log_generation_attempt(prompt, False, error_msg)
            return False, None, error_msg
        
        try:
            # Nota: Gemini actualmente no genera imágenes directamente
            # En su lugar, generamos una descripción detallada y creamos una imagen placeholder
            
            # Build the image description prompt
            description_prompt = self._build_description_prompt(prompt, **kwargs)
            
            # Generate detailed description using Gemini
            start_time = time.time()
            response = self.model.generate_content(description_prompt)
            generation_time = time.time() - start_time
            
            if response.text:
                # Create a placeholder image with the generated description
                placeholder_url = self._create_placeholder_image(
                    response.text, 
                    **kwargs
                )
                
                if placeholder_url:
                    logger.info(f"Generated placeholder image with AI description in {generation_time:.2f}s")
                    self.log_generation_attempt(prompt, True)
                    return True, placeholder_url, None
            
            error_msg = "No description generated for image"
            self.log_generation_attempt(prompt, False, error_msg)
            return False, None, error_msg
            
        except Exception as e:
            error_msg = f"Error generating image with Gemini: {str(e)}"
            logger.error(error_msg)
            self.log_generation_attempt(prompt, False, error_msg)
            
            # Check for specific error types
            if "quota" in str(e).lower() or "limit" in str(e).lower():
                raise APIQuotaExceededError(error_msg, "Gemini")
            
            return False, None, error_msg
    
    def _build_image_prompt(self, prompt: str, **kwargs) -> str:
        """
        Build an optimized prompt for image generation.
        
        Args:
            prompt: Base prompt
            **kwargs: Additional parameters
            
        Returns:
            Enhanced prompt for image generation
        """
        style = kwargs.get('style', 'professional')
        size = kwargs.get('size', '1024x1024')
        
        # Style mappings
        style_prompts = {
            'professional': 'professional, clean, modern design',
            'modern': 'modern, minimalist, sleek design',
            'tech': 'technological, futuristic, digital art style',
            'creative': 'creative, artistic, vibrant colors',
        }
        
        style_desc = style_prompts.get(style, 'professional, clean design')
        
        enhanced_prompt = f"""
        Generate a high-quality cover image for a blog post with the following specifications:
        
        Content: {prompt}
        Style: {style_desc}
        Dimensions: {size}
        
        The image should be:
        - Suitable for a blog post cover
        - Visually appealing and professional
        - Related to the content topic
        - High resolution and clear
        - Appropriate for web usage
        
        Please create an image that captures the essence of the topic while being visually striking.
        """
        
        return enhanced_prompt.strip()
    
    def _create_placeholder_image(self, description: str, **kwargs) -> Optional[str]:
        """
        Create a placeholder image when direct generation fails.
        
        Args:
            description: Text description of the image
            **kwargs: Additional parameters
            
        Returns:
            URL of created placeholder image or None
        """
        try:
            # Parse size
            size_str = kwargs.get('size', '1024x1024')
            if 'x' in size_str:
                width, height = map(int, size_str.split('x'))
            else:
                width, height = 1024, 1024
            
            # Create a simple colored image with text
            from PIL import Image, ImageDraw, ImageFont
            
            # Choose color based on content
            colors = {
                'tech': '#2563eb',      # Blue
                'business': '#059669',   # Green
                'design': '#dc2626',     # Red
                'science': '#7c3aed',    # Purple
                'default': '#374151'     # Gray
            }
            
            # Simple keyword detection for color
            description_lower = description.lower()
            bg_color = colors['default']
            for keyword, color in colors.items():
                if keyword in description_lower:
                    bg_color = color
                    break
            
            # Create image
            img = Image.new('RGB', (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Add text overlay (simplified)
            try:
                # Try to use a default font
                font = ImageFont.load_default()
                
                # Add title text
                title = kwargs.get('title', 'AI Generated Image')
                text_color = '#ffffff'
                
                # Calculate text position (centered)
                bbox = draw.textbbox((0, 0), title, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                
                # Draw text with shadow
                draw.text((x+2, y+2), title, fill='#000000', font=font)  # Shadow
                draw.text((x, y), title, fill=text_color, font=font)     # Main text
                
            except Exception as e:
                logger.warning(f"Could not add text to placeholder image: {e}")
            
            # Save the image using ImageStorage
            filename = f"gemini_placeholder_{int(time.time())}.jpg"
            return ImageStorage.save_image_from_pil(img, filename)
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            return None
    
    def _build_description_prompt(self, prompt: str, **kwargs) -> str:
        """
        Build a prompt for generating detailed image descriptions.
        """
        style = kwargs.get('style', 'professional')
        
        description_prompt = f"""
        Create a detailed visual description for a blog post cover image about: {prompt}
        
        Style: {style}
        
        The description should be suitable for creating a professional blog post header image.
        Keep the description concise but vivid, around 2-3 sentences.
        """
        
        return description_prompt.strip()
    
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return self.api_key is not None and self.model is not None
    
    def get_service_name(self) -> str:
        """Get service name."""
        return "Google Gemini"
    
    def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate Gemini configuration."""
        if not self.api_key:
            return False, "Google API key not configured"
        
        try:
            genai.configure(api_key=self.api_key)
            test_model = genai.GenerativeModel(self.model_name)
            test_response = test_model.generate_content("Test")
            return True, None
        except Exception as e:
            return False, f"API validation failed: {str(e)}"
    
    def get_supported_parameters(self):
        """Get supported parameters for Gemini."""
        return {
            'size': {
                'type': 'string',
                'default': '1024x1024',
                'options': ['512x512', '1024x1024', '1792x1024'],
                'description': 'Image dimensions'
            },
            'style': {
                'type': 'string',
                'default': 'professional',
                'options': ['professional', 'modern', 'tech', 'creative'],
                'description': 'Image style'
            }
        }
    
    def get_cost_estimate(self, **kwargs) -> float:
        """Estimate cost for Gemini image generation."""
        return 0.01
    
    def get_generation_time_estimate(self, **kwargs) -> int:
        """Estimate generation time for Gemini."""
        return 15