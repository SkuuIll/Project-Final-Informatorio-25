"""
Test para verificar que la subida de imágenes de CKEditor funcione correctamente.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
import json


class CKEditorUploadTestCase(TestCase):
    """Test case para subida de imágenes de CKEditor."""
    
    def setUp(self):
        """Configurar datos de prueba."""
        self.client = Client()
        
        # Crear usuario
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Iniciar sesión
        self.client.login(username='testuser', password='testpass123')
    
    def create_test_image(self, size=(100, 100), format='JPEG'):
        """Crear una imagen de prueba."""
        img = Image.new('RGB', size, color='red')
        
        img_io = BytesIO()
        img.save(img_io, format=format, quality=85)
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test_image.{format.lower()}',
            content=img_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_upload_valid_image(self):
        """Probar subida de imagen válida."""
        test_image = self.create_test_image()
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': test_image
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('url', data)
        self.assertTrue(data['url'].endswith('.jpg') or data['url'].endswith('.jpeg'))
    
    def test_upload_large_image(self):
        """Probar subida de imagen demasiado grande."""
        # Crear imagen de 6MB (más grande que el límite de 5MB)
        large_image = self.create_test_image(size=(3000, 3000))
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': large_image
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('demasiado grande', data['error']['message'])
    
    def test_upload_invalid_file_type(self):
        """Probar subida de archivo no válido."""
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': invalid_file
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_upload_without_authentication(self):
        """Probar subida sin autenticación."""
        self.client.logout()
        
        test_image = self.create_test_image()
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': test_image
        })
        
        # Debería redirigir al login
        self.assertEqual(response.status_code, 302)
    
    def test_upload_empty_file(self):
        """Probar subida de archivo vacío."""
        empty_file = SimpleUploadedFile(
            name='empty.jpg',
            content=b'',
            content_type='image/jpeg'
        )
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': empty_file
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('vacío', data['error']['message'])
    
    def test_upload_without_file(self):
        """Probar subida sin archivo."""
        response = self.client.post('/ckeditor5/upload/', {})
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)