"""
Test de integración con las vistas.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch, Mock
from posts.models import Post
from posts.forms import AiPostGeneratorForm


class TestViewIntegration(TestCase):
    """Test de integración con las vistas"""
    
    def setUp(self):
        """Configuración inicial"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create profile for the user
        from accounts.models import Profile
        Profile.objects.get_or_create(user=self.user, defaults={'can_post': True})
        
        self.client.login(username='testuser', password='testpass123')
        
    def test_ai_generator_view_get(self):
        """Test GET request to AI generator view"""
        
        with patch('posts.views.ImageSelector') as mock_selector:
            mock_selector.get_suitable_cover_images.return_value = []
            
            response = self.client.get('/generate-ai-post/')
            
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'generate_cover_image')
            self.assertContains(response, 'cover_image_style')
            
    @patch('posts.views.generate_complete_post')
    def test_ai_generator_view_post_success(self, mock_generate):
        """Test successful POST request to AI generator view"""
        
        # Mock successful generation
        mock_generate.return_value = {
            'success': True,
            'title': 'Test Generated Title',
            'content': 'Test generated content',
            'tags': ['test', 'ai'],
            'reading_time': 2,
            'cover_image_url': '/media/covers/test.jpg'
        }
        
        form_data = {
            'url': 'https://example.com/test',
            'rewrite_prompt': 'Test prompt',
            'extract_images': True,
            'max_images': 3,
            'generate_cover_image': True,
            'cover_image_style': 'professional',
            'status': 'draft'
        }
        
        response = self.client.post('/generate-ai-post/', data=form_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Verify post was created
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.title, 'Test Generated Title')
        self.assertEqual(post.content, 'Test generated content')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.status, 'draft')
        
        # Verify generate_complete_post was called with correct parameters
        mock_generate.assert_called_once_with(
            url='https://example.com/test',
            rewrite_prompt='Test prompt',
            extract_images=True,
            max_images=3,
            title=None,
            generate_cover=True,
            image_style='professional'
        )
        
    @patch('posts.views.generate_complete_post')
    def test_ai_generator_view_post_failure(self, mock_generate):
        """Test POST request with generation failure"""
        
        # Mock generation failure
        mock_generate.return_value = {
            'success': False,
            'error': 'Failed to extract content from URL'
        }
        
        form_data = {
            'url': 'https://invalid-url.com/test',
            'rewrite_prompt': 'Test prompt',
            'status': 'draft'
        }
        
        response = self.client.post('/generate-ai-post/', data=form_data)
        
        # Should not redirect, should show form with error
        self.assertEqual(response.status_code, 200)
        
        # Should not create a post
        self.assertEqual(Post.objects.count(), 0)
        
        # Should show error message
        messages = list(response.context['messages'])
        self.assertTrue(any('Failed to extract content from URL' in str(m) for m in messages))
        
    def test_form_validation(self):
        """Test form validation with new fields"""
        
        # Valid form data
        form_data = {
            'url': 'https://example.com/test',
            'rewrite_prompt': 'Test prompt',
            'extract_images': True,
            'max_images': 5,
            'generate_cover_image': True,
            'cover_image_style': 'modern',
            'use_existing_image': False,
            'status': 'draft'
        }
        
        form = AiPostGeneratorForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Test invalid max_images
        form_data['max_images'] = 25  # Over limit
        form = AiPostGeneratorForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    @patch('posts.views.generate_complete_post')
    def test_custom_title_handling(self, mock_generate):
        """Test handling of custom title"""
        
        mock_generate.return_value = {
            'success': True,
            'title': 'Custom Title',
            'content': 'Test content',
            'tags': ['custom'],
            'reading_time': 1
        }
        
        form_data = {
            'title': 'Custom Title',
            'rewrite_prompt': 'Test prompt',
            'generate_cover_image': False,
            'status': 'draft'
        }
        
        response = self.client.post('/generate-ai-post/', data=form_data)
        
        # Verify title parameter was passed
        mock_generate.assert_called_once()
        call_kwargs = mock_generate.call_args.kwargs
        self.assertEqual(call_kwargs['title'], 'Custom Title')
        
        # Verify post was created with custom title
        post = Post.objects.first()
        self.assertEqual(post.title, 'Custom Title')
        
    def test_login_required(self):
        """Test that login is required"""
        
        self.client.logout()
        response = self.client.get('/generate-ai-post/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        
    @patch('posts.views.generate_complete_post')
    def test_tag_handling(self, mock_generate):
        """Test handling of generated tags"""
        
        mock_generate.return_value = {
            'success': True,
            'title': 'Test Title',
            'content': 'Test content',
            'tags': ['python', 'django', 'ai', 'machine-learning'],
            'reading_time': 3
        }
        
        form_data = {
            'url': 'https://example.com/test',
            'rewrite_prompt': 'Test prompt',
            'status': 'draft'
        }
        
        response = self.client.post('/generate-ai-post/', data=form_data)
        
        # Verify post was created with tags
        post = Post.objects.first()
        tag_names = [tag.name for tag in post.tags.all()]
        
        self.assertIn('python', tag_names)
        self.assertIn('django', tag_names)
        self.assertIn('ai', tag_names)
        self.assertIn('machine-learning', tag_names)
        
    @patch('posts.views.generate_complete_post')
    def test_reading_time_saved(self, mock_generate):
        """Test that reading time is saved to post"""
        
        mock_generate.return_value = {
            'success': True,
            'title': 'Test Title',
            'content': 'Test content',
            'tags': ['test'],
            'reading_time': 7
        }
        
        form_data = {
            'url': 'https://example.com/test',
            'rewrite_prompt': 'Test prompt',
            'status': 'draft'
        }
        
        response = self.client.post('/generate-ai-post/', data=form_data)
        
        # Verify reading time was saved
        post = Post.objects.first()
        self.assertEqual(post.reading_time, 7)
        
    def test_form_field_defaults(self):
        """Test default values of form fields"""
        
        form = AiPostGeneratorForm()
        
        # Check default values
        self.assertTrue(form.fields['generate_cover_image'].initial)
        self.assertEqual(form.fields['cover_image_style'].initial, 'professional')
        self.assertFalse(form.fields['use_existing_image'].initial)
        self.assertTrue(form.fields['extract_images'].initial)
        self.assertEqual(form.fields['max_images'].initial, 5)
        
    def test_form_style_choices(self):
        """Test style choices in form"""
        
        form = AiPostGeneratorForm()
        style_choices = dict(form.fields['cover_image_style'].choices)
        
        expected_styles = {
            'professional': 'Profesional - Limpio y corporativo',
            'modern': 'Moderno - Minimalista y contemporáneo',
            'tech': 'Tecnológico - Digital y futurista',
            'creative': 'Creativo - Artístico y vibrante'
        }
        
        for key, value in expected_styles.items():
            self.assertEqual(style_choices[key], value)