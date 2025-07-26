"""
Tests for cover image prompt builder.
"""

from django.test import TestCase
from posts.image_generation.prompt_builder import CoverImagePromptBuilder


class TestCoverImagePromptBuilder(TestCase):
    """Test the cover image prompt builder."""
    
    def test_extract_keywords_from_title(self):
        """Test keyword extraction from title."""
        title = "How to Build REST APIs with Django and Python"
        keywords = CoverImagePromptBuilder.extract_keywords(title)
        
        # Check that meaningful keywords are extracted
        self.assertIn('build', keywords)
        self.assertIn('rest', keywords)
        self.assertIn('apis', keywords)
        
        # Check that stop words are filtered out
        self.assertNotIn('how', keywords)
        self.assertNotIn('to', keywords)
        self.assertNotIn('with', keywords)
    
    def test_extract_keywords_with_tags(self):
        """Test keyword extraction with tags."""
        title = "Machine Learning Tutorial"
        tags = ['python', 'ai', 'tutorial', 'data-science']
        
        keywords = CoverImagePromptBuilder.extract_keywords(title, tags=tags)
        
        # Tags should have priority and be included
        self.assertIn('python', keywords)
        self.assertIn('ai', keywords)
        
        # Title keywords should also be included
        self.assertIn('machine', keywords)
        self.assertIn('learning', keywords)
    
    def test_extract_keywords_with_content(self):
        """Test keyword extraction with content."""
        title = "Web Development"
        content = "<p>This article covers React, JavaScript, and modern web development practices.</p>"
        
        keywords = CoverImagePromptBuilder.extract_keywords(title, content=content)
        
        self.assertIn('react', keywords)
        self.assertIn('javascript', keywords)
        self.assertIn('development', keywords)
    
    def test_build_professional_prompt(self):
        """Test building a professional style prompt."""
        title = "Django REST API Tutorial"
        tags = ['django', 'python', 'api']
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            tags=tags,
            style='professional'
        )
        
        self.assertIn('professional', prompt.lower())
        self.assertIn('django', prompt.lower())
        self.assertIn('api', prompt.lower())
        self.assertIn('clean', prompt.lower())
        self.assertIn('corporate', prompt.lower())
    
    def test_build_tech_prompt(self):
        """Test building a tech style prompt."""
        title = "Machine Learning with Python"
        tags = ['python', 'ml', 'ai']
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            tags=tags,
            style='tech'
        )
        
        self.assertIn('technological', prompt.lower())
        self.assertIn('futuristic', prompt.lower())
        self.assertIn('python', prompt.lower())
        self.assertIn('machine learning', prompt.lower())
    
    def test_build_modern_prompt(self):
        """Test building a modern style prompt."""
        title = "React Hooks Guide"
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            style='modern'
        )
        
        self.assertIn('modern', prompt.lower())
        self.assertIn('contemporary', prompt.lower())
        self.assertIn('minimalist', prompt.lower())
    
    def test_build_creative_prompt(self):
        """Test building a creative style prompt."""
        title = "Creative Coding with p5.js"
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            style='creative'
        )
        
        self.assertIn('creative', prompt.lower())
        self.assertIn('artistic', prompt.lower())
        self.assertIn('vibrant', prompt.lower())
    
    def test_technical_context_detection(self):
        """Test detection of technical context."""
        title = "Python Django Tutorial"
        keywords = ['python', 'django', 'web']
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            tags=keywords
        )
        
        # Should include technical context for Python and Django
        self.assertIn('python', prompt.lower())
        self.assertIn('django', prompt.lower())
    
    def test_get_style_options(self):
        """Test getting available style options."""
        styles = CoverImagePromptBuilder.get_style_options()
        
        self.assertIn('professional', styles)
        self.assertIn('modern', styles)
        self.assertIn('tech', styles)
        self.assertIn('creative', styles)
        
        # Check descriptions are provided
        self.assertTrue(all(isinstance(desc, str) and len(desc) > 0 
                          for desc in styles.values()))
    
    def test_validate_prompt_valid(self):
        """Test validation of valid prompt."""
        prompt = "Create a professional blog post cover image about Django development"
        
        is_valid, error = CoverImagePromptBuilder.validate_prompt(prompt)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_prompt_too_short(self):
        """Test validation of too short prompt."""
        prompt = "Short"
        
        is_valid, error = CoverImagePromptBuilder.validate_prompt(prompt)
        
        self.assertFalse(is_valid)
        self.assertIn('too short', error)
    
    def test_validate_prompt_too_long(self):
        """Test validation of too long prompt."""
        prompt = "A" * 2001  # Exceeds 2000 character limit
        
        is_valid, error = CoverImagePromptBuilder.validate_prompt(prompt)
        
        self.assertFalse(is_valid)
        self.assertIn('too long', error)
    
    def test_validate_prompt_missing_elements(self):
        """Test validation of prompt missing required elements."""
        prompt = "This is just some random text without the required elements"
        
        is_valid, error = CoverImagePromptBuilder.validate_prompt(prompt)
        
        self.assertFalse(is_valid)
        self.assertIn('blog', error.lower())
    

    
    def test_optimize_prompt_for_stability(self):
        """Test prompt optimization for Stability AI."""
        base_prompt = """Create a professional image
        Visual Elements:
        - Main topic: Django
        Style: professional
        Colors: blue, white
        Technical Requirements:
        - High quality
        Avoid: text overlays"""
        
        optimized = CoverImagePromptBuilder.optimize_prompt_for_service(
            base_prompt, 'stability'
        )
        
        # Should be more concise for Stability AI
        self.assertIn('create', optimized.lower())
        self.assertIn('visual elements', optimized.lower())
        self.assertIn('style:', optimized.lower())
    
    def test_optimize_prompt_for_gemini(self):
        """Test prompt optimization for Gemini."""
        base_prompt = "Create a professional image about Django"
        
        optimized = CoverImagePromptBuilder.optimize_prompt_for_service(
            base_prompt, 'gemini'
        )
        
        # Gemini should have structured instructions
        self.assertIn('generate a professional blog cover image', optimized.lower())
        self.assertIn(base_prompt.lower(), optimized.lower())
    
    def test_keyword_extraction_filters_stop_words(self):
        """Test that keyword extraction filters out stop words."""
        title = "The Best Way to Learn Python Programming"
        
        keywords = CoverImagePromptBuilder.extract_keywords(title)
        
        # Should not include stop words
        stop_words = ['the', 'to', 'way']
        for stop_word in stop_words:
            self.assertNotIn(stop_word, keywords)
        
        # Should include meaningful words
        self.assertIn('python', keywords)
        self.assertIn('programming', keywords)
        self.assertIn('learn', keywords)
    
    def test_keyword_extraction_handles_spanish(self):
        """Test keyword extraction with Spanish stop words."""
        title = "Cómo crear una API REST con Django y Python"
        
        keywords = CoverImagePromptBuilder.extract_keywords(title)
        
        # Should not include Spanish stop words
        spanish_stop_words = ['cómo', 'una', 'con']
        for stop_word in spanish_stop_words:
            self.assertNotIn(stop_word, keywords)
        
        # Should include meaningful words
        self.assertIn('django', keywords)
        self.assertIn('python', keywords)
        self.assertIn('crear', keywords)
    
    def test_main_topic_detection(self):
        """Test main topic detection from title and keywords."""
        title = "Building APIs with Django REST Framework"
        keywords = ['django', 'api', 'rest', 'framework']
        
        main_topic = CoverImagePromptBuilder._get_main_topic(title, keywords)
        
        # Should detect Django as main technical topic
        self.assertIn('django', main_topic.lower())
    
    def test_additional_context_inclusion(self):
        """Test inclusion of additional context in prompt."""
        title = "Python Tutorial"
        additional_context = "Focus on beginner-friendly design"
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            additional_context=additional_context
        )
        
        self.assertIn(additional_context, prompt)
    
    def test_size_parameter_inclusion(self):
        """Test that size parameter is included in prompt."""
        title = "Django Tutorial"
        size = "1792x1024"
        
        prompt = CoverImagePromptBuilder.build_cover_prompt(
            title=title,
            size=size
        )
        
        self.assertIn(size, prompt)