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
            # Build the image generation prompt
            image_prompt = self._build_image_prompt(prompt, **kwargs)
            
            # Generate image using Gemini
            start_time = time.time()
            response = self.model.generate_content([image_prompt])
            generation_time = time.time() - start_time
            
            # Check if response contains an image
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Save the generated image
                        image_data = part.inline_data.data
                        image_url = ImageStorage.save_image_from_content(
                            image_data, 
                            filename=f"gemini_generated_{int(time.time())}.jpg"
                        )
                        
                        if image_url:
                            logger.info(f"Image generated successfully in {generation_time:.2f}s")
                            self.log_generation_attempt(prompt, True)
                            return True, image_url, None
            
            # If no image in response, try alternative approach only if enabled
            if kwargs.get('allow_placeholder', False):
                # Generate a detailed description and use it to create a simple colored image
                description_prompt = f"Create a detailed visual description for: {prompt}"
                description_response = self.model.generate_content(description_prompt)
                
                if description_response.text:
                    # Create a placeholder image with the description
                    placeholder_url = self._create_placeholder_image(
                        description_response.text, 
                        **kwargs
                    )
                    
                    if placeholder_url:
                        logger.info("Generated placeholder image with description")
                        self.log_generation_attempt(prompt, True)
                        return True, placeholder_url, None
            
            error_msg = "No image generated in response"
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
            except:
                font = None
            
            # Add title text
            text = "Generated Cover Image"
            if font:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                x = (width - text_width) // 2
                y = (height - text_height) // 2
                draw.text((x, y), text, fill='white', font=font)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                img.save(temp_file.name, 'JPEG', quality=85)
                temp_path = temp_file.name
            
            # Process and save the image
            processed_path = ImageProcessor.optimize_image(temp_path)
            
            # Save to storage
            with open(processed_path, 'rb') as f:
                image_content = f.read()
            
            image_url = ImageStorage.save_image_from_content(
                image_content,
                filename=f"placeholder_{int(time.time())}.jpg"
            )
            
            # Cleanup temp files
            ImageStorage.cleanup_temp_files([temp_path, processed_path])
            
            return image_url
            
        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            return None
    
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
            # Test API connection
            genai.configure(api_key=self.api_key)
            test_model = genai.GenerativeModel(self.model_name)
            # Simple test to verify API works
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
            },
            'model': {
                'type': 'string',
                'default': 'gemini-2.0-flash-exp',
                'options': ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash'],
                'description': 'Gemini model to use'
            }
        }
    
    def get_cost_estimate(self, **kwargs) -> float:
        """Estimate cost for Gemini image generation."""
        # Gemini pricing is generally lower than other services
        # This is an estimate - actual costs may vary
        return 0.01  # Estimated $0.01 per image
    
    def get_generation_time_estimate(self, **kwargs) -> int:
        """Estimate generation time for Gemini."""
        return 15  # Estimated 15 seconds