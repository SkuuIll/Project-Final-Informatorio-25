"""
Tests para verificar que los likes y favoritos funcionan correctamente.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from posts.models import Post, Comment
import json


class LikesFavoritesTestCase(TestCase):
    """Test case para likes y favoritos."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.client = Client()
        
        # Crear usuario que dará likes
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear autor del post (diferente usuario)
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='authorpass123'
        )
        
        # Crear post del autor
        self.post = Post.objects.create(
            title='Test Post',
            content='Este es un post de prueba',
            author=self.author,
            status='published'
        )
        
        # Crear comentario del autor
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.author,
            content='Test comment'
        )
        
        # Iniciar sesión
        self.client.login(username='testuser', password='testpass123')
    
    def test_like_post_authenticated(self):
        """Probar like en post con usuario autenticado."""
        url = reverse('posts:like_post', kwargs={
            'username': self.author.username, 
            'slug': self.post.slug
        })
        
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)
    
    def test_like_comment_authenticated(self):
        """Probar like en comentario con usuario autenticado."""
        url = reverse('posts:like_comment', kwargs={'pk': self.comment.pk})
        
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)
    
    def test_favorite_post_authenticated(self):
        """Probar favorito con usuario autenticado."""
        url = reverse('posts:favorite_post', kwargs={
            'username': self.author.username, 
            'slug': self.post.slug
        })
        
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertTrue(data['favorited'])
        self.assertEqual(data['favorites_count'], 1)
    
    def test_like_post_unauthenticated(self):
        """Probar like en post sin autenticación."""
        self.client.logout()
        
        url = reverse('posts:like_post', kwargs={
            'username': self.author.username, 
            'slug': self.post.slug
        })
        
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 401)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('iniciar sesión', data['error'])
    
    def test_toggle_like_post(self):
        """Probar toggle de like (dar y quitar like)."""
        url = reverse('posts:like_post', kwargs={
            'username': self.author.username, 
            'slug': self.post.slug
        })
        
        # Dar like
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['likes_count'], 1)
        
        # Quitar like
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['likes_count'], 0)
    
    def test_toggle_favorite_post(self):
        """Probar toggle de favorito (agregar y quitar)."""
        url = reverse('posts:favorite_post', kwargs={
            'username': self.author.username, 
            'slug': self.post.slug
        })
        
        # Agregar a favoritos
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data = response.json()
        self.assertTrue(data['favorited'])
        self.assertEqual(data['favorites_count'], 1)
        
        # Quitar de favoritos
        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        data = response.json()
        self.assertFalse(data['favorited'])
        self.assertEqual(data['favorites_count'], 0)