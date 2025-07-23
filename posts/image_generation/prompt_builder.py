"""
Cover image prompt builder system for generating optimized prompts.
"""

import re
from typing import List, Dict, Optional
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class CoverImagePromptBuilder:
    """
    Builder class for creating optimized prompts for cover image generation.
    """
    
    # Style-specific prompt enhancements
    STYLE_PROMPTS = {
        'professional': {
            'description': 'clean, corporate, business-like, professional appearance',
            'colors': 'neutral colors, blues, grays, whites',
            'elements': 'minimal design, clean lines, professional typography',
            'avoid': 'cartoonish, overly colorful, casual elements'
        },
        'modern': {
            'description': 'contemporary, sleek, minimalist, cutting-edge design',
            'colors': 'modern color palette, gradients, bold accents',
            'elements': 'geometric shapes, clean typography, negative space',
            'avoid': 'vintage elements, cluttered design, old-fashioned styles'
        },
        'tech': {
            'description': 'technological, futuristic, digital, high-tech aesthetic',
            'colors': 'tech colors like blue, green, purple, neon accents',
            'elements': 'circuit patterns, digital elements, code snippets, screens',
            'avoid': 'organic shapes, handwritten elements, traditional designs'
        },
        'creative': {
            'description': 'artistic, imaginative, vibrant, creative expression',
            'colors': 'vibrant colors, artistic palette, creative combinations',
            'elements': 'artistic elements, creative typography, unique compositions',
            'avoid': 'boring layouts, corporate stiffness, monochrome designs'
        }
    }
    
    # Common technical keywords and their visual representations
    TECH_KEYWORDS = {
        'python': 'Python programming language logo, code snippets, snake motifs',
        'javascript': 'JavaScript code, web development, browser elements',
        'react': 'React components, modern web interface, component trees',
        'django': 'Django framework, web development, Python web apps',
        'api': 'API connections, data flow, network diagrams',
        'database': 'database icons, data structures, server racks',
        'machine learning': 'neural networks, AI brain, data patterns',
        'artificial intelligence': 'AI brain, neural networks, robot elements',
        'web development': 'websites, browsers, responsive design',
        'mobile': 'smartphones, mobile apps, responsive interfaces',
        'cloud': 'cloud computing, servers, distributed systems',
        'security': 'locks, shields, encryption symbols',
        'blockchain': 'chain links, cryptocurrency, distributed ledger',
        'devops': 'deployment pipelines, automation, server management'
    }
    
    @classmethod
    def build_cover_prompt(
        cls, 
        title: str, 
        content: str = "", 
        tags: List[str] = None, 
        style: str = 'professional',
        size: str = '1024x1024',
        additional_context: str = ""
    ) -> str:
        """
        Build an optimized prompt for cover image generation.
        
        Args:
            title: Post title
            content: Post content (optional)
            tags: Post tags (optional)
            style: Image style preference
            size: Target image dimensions
            additional_context: Additional context or requirements
            
        Returns:
            Optimized prompt string
        """
        # Extract keywords from title and content
        keywords = cls.extract_keywords(title, content, tags)
        
        # Get style-specific enhancements
        style_info = cls.STYLE_PROMPTS.get(style, cls.STYLE_PROMPTS['professional'])
        
        # Build the main prompt
        prompt_parts = [
            f"Create a {style_info['description']} blog post cover image about: {title}",
            "",
            "Visual Elements:",
            f"- Main topic: {cls._get_main_topic(title, keywords)}",
            f"- Key concepts: {', '.join(keywords[:5])}",
            f"- Style: {style_info['description']}",
            f"- Colors: {style_info['colors']}",
            f"- Design elements: {style_info['elements']}",
            "",
            "Technical Requirements:",
            f"- Dimensions: {size}",
            "- High quality, professional appearance",
            "- Suitable for blog post header/cover",
            "- Clear, readable, and visually appealing",
            "- No text overlays or watermarks",
            "",
            f"Avoid: {style_info['avoid']}, text overlays, watermarks, logos"
        ]
        
        # Add technical context if relevant
        tech_context = cls._get_technical_context(keywords)
        if tech_context:
            prompt_parts.insert(-2, f"Technical context: {tech_context}")
        
        # Add additional context if provided
        if additional_context:
            prompt_parts.insert(-2, f"Additional requirements: {additional_context}")
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def extract_keywords(
        cls, 
        title: str, 
        content: str = "", 
        tags: List[str] = None, 
        max_keywords: int = 8
    ) -> List[str]:
        """
        Extract relevant keywords from title, content, and tags.
        
        Args:
            title: Post title
            content: Post content
            tags: Post tags
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        keywords = []
        
        # Add tags first (highest priority)
        if tags:
            keywords.extend([tag.lower().strip() for tag in tags[:3]])
        
        # Extract from title
        title_keywords = cls._extract_from_text(title)
        keywords.extend(title_keywords[:3])
        
        # Extract from content if available
        if content:
            content_text = strip_tags(content)[:500]  # First 500 chars
            content_keywords = cls._extract_from_text(content_text)
            keywords.extend(content_keywords[:3])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen and len(keyword) > 2:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords[:max_keywords]
    
    @classmethod
    def _extract_from_text(cls, text: str) -> List[str]:
        """Extract keywords from text using simple NLP techniques."""
        if not text:
            return []
        
        # Clean and normalize text
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'como', 'para', 'con', 'por', 'una', 'uno',
            'del', 'las', 'los', 'que', 'más', 'muy', 'también', 'puede', 'hacer',
            'how', 'what', 'when', 'where', 'why', 'who'
        }
        
        # Extract meaningful words (lowered minimum length)
        keywords = []
        for word in words:
            if (len(word) > 2 and  # Changed from 3 to 2 to catch 'api'
                word not in stop_words and 
                not word.isdigit()):
                keywords.append(word)
        
        # Return most relevant keywords (simple frequency-based)
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_keywords[:10]]
    
    @classmethod
    def _get_main_topic(cls, title: str, keywords: List[str]) -> str:
        """Determine the main topic from title and keywords."""
        # Check for technical topics first
        title_lower = title.lower()
        
        for tech_term, description in cls.TECH_KEYWORDS.items():
            if tech_term in title_lower or tech_term in [k.lower() for k in keywords]:
                return f"{tech_term} - {description.split(',')[0]}"
        
        # Fallback to first few keywords
        if keywords:
            return f"{title} - focusing on {', '.join(keywords[:3])}"
        
        return title
    
    @classmethod
    def _get_technical_context(cls, keywords: List[str]) -> str:
        """Get technical context based on keywords."""
        tech_contexts = []
        
        for keyword in keywords:
            if keyword.lower() in cls.TECH_KEYWORDS:
                tech_contexts.append(cls.TECH_KEYWORDS[keyword.lower()])
        
        if tech_contexts:
            return "; ".join(tech_contexts[:2])  # Limit to 2 contexts
        
        return ""
    
    @classmethod
    def get_style_options(cls) -> Dict[str, str]:
        """Get available style options with descriptions."""
        return {
            style: info['description'] 
            for style, info in cls.STYLE_PROMPTS.items()
        }
    
    @classmethod
    def validate_prompt(cls, prompt: str) -> tuple[bool, Optional[str]]:
        """
        Validate a generated prompt.
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not prompt or len(prompt.strip()) < 10:
            return False, "Prompt is too short"
        
        if len(prompt) > 2000:
            return False, "Prompt is too long (max 2000 characters)"
        
        # Check for required elements
        required_elements = ['create', 'image', 'blog']
        if not any(element in prompt.lower() for element in required_elements):
            return False, "Prompt should mention creating an image for a blog"
        
        return True, None
    
    @classmethod
    def optimize_prompt_for_service(cls, prompt: str, service: str) -> str:
        """
        Optimize prompt for specific image generation service.
        
        Args:
            prompt: Base prompt
            service: Target service ('openai', 'stability', 'gemini')
            
        Returns:
            Service-optimized prompt
        """
        if service == 'openai':
            # DALL-E works well with detailed, descriptive prompts
            return prompt
        
        elif service == 'stability':
            # Stability AI prefers more concise, artistic descriptions
            lines = prompt.split('\n')
            # Keep main description and key visual elements
            optimized_lines = []
            for line in lines:
                if any(keyword in line.lower() for keyword in 
                      ['create', 'visual elements', 'style:', 'colors:', 'technical context']):
                    optimized_lines.append(line)
            
            return '\n'.join(optimized_lines) if optimized_lines else prompt
        
        elif service == 'gemini':
            # Gemini works well with structured, clear instructions
            return f"Generate a professional blog cover image.\n\n{prompt}"
        
        return prompt