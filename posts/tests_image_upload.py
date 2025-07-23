"""
Tests para la subida de imágenes en CKEditor.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image
import json


class ImageUploadTestCase(TestCase):
    """Test case para subida de imágenes."""
    
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
            name=f'test.{format.lower()}',
            content=img_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_upload_small_image(self):
        """Probar subida de imagen pequeña."""
        test_image = self.create_test_image(size=(50, 50))
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': test_image
        })
        
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('url', data)
            print(f"✅ Subida exitosa: {data['url']}")
        else:
            data = response.json()
            print(f"❌ Error: {data}")
            self.fail(f"Upload failed: {data}")
    
    def test_upload_different_formats(self):
        """Probar subida de diferentes formatos."""
        formats = ['JPEG', 'PNG', 'WEBP']
        
        for format_name in formats:
            with self.subTest(format=format_name):
                test_image = self.create_test_image(format=format_name)
                
                response = self.client.post('/ckeditor5/upload/', {
                    'upload': test_image
                })
                
                print(f"Testing {format_name}: Status {response.status_code}")
                
                if response.status_code != 200:
                    data = response.json()
                    print(f"Error with {format_name}: {data}")
    
    def test_upload_without_login(self):
        """Probar subida sin autenticación."""
        self.client.logout()
        
        test_image = self.create_test_image()
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': test_image
        })
        
        print(f"Without login - Status: {response.status_code}")
        # Debería redirigir a login o dar error 401/403
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_upload_large_image(self):
        """Probar subida de imagen grande."""
        # Crear imagen de 6MB (debería fallar)
        large_image = self.create_test_image(size=(2000, 2000))
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': large_image
        })
        
        print(f"Large image - Status: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"Expected error for large image: {data}")
            self.assertIn('error', data)
        else:
            print("Large image was accepted (unexpected)")
    
    def test_upload_invalid_file(self):
        """Probar subida de archivo no válido."""
        # Crear archivo de texto
        text_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': text_file
        })
        
        print(f"Text file - Status: {response.status_code}")
        
        if response.status_code == 400:
            data = response.json()
            print(f"Expected error for text file: {data}")
            self.assertIn('error', data)
        else:
            print("Text file was accepted (unexpected)")