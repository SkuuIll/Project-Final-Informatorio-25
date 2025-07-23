"""
Test para debuggear problemas de subida de imágenes en CKEditor.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
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
        img.save(img_io, format=format)
        img_io.seek(0)
        
        return SimpleUploadedFile(
            name=f'test.{format.lower()}',
            content=img_io.getvalue(),
            content_type=f'image/{format.lower()}'
        )
    
    def test_small_image_upload(self):
        """Probar subida de imagen pequeña."""
        # Crear imagen muy pequeña (50x50)
        test_image = self.create_test_image(size=(50, 50))
        
        print(f"Tamaño de imagen: {test_image.size} bytes")
        print(f"Content type: {test_image.content_type}")
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': test_image
        })
        
        print(f"Status code: {response.status_code}")
        print(f"Response content: {response.content.decode()}")
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn('url', data)
            print(f"✅ Imagen subida exitosamente: {data['url']}")
        else:
            if response.content:
                try:
                    error_data = response.json()
                    print(f"❌ Error: {error_data}")
                except:
                    print(f"❌ Error sin JSON: {response.content.decode()}")
            self.fail(f"Upload failed with status {response.status_code}")
    
    def test_different_formats(self):
        """Probar diferentes formatos de imagen."""
        formats = ['JPEG', 'PNG']
        
        for format_type in formats:
            with self.subTest(format=format_type):
                test_image = self.create_test_image(size=(50, 50), format=format_type)
                
                response = self.client.post('/ckeditor5/upload/', {
                    'upload': test_image
                })
                
                print(f"Formato {format_type}: Status {response.status_code}")
                
                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        print(f"Error para {format_type}: {error_data}")
                    except:
                        print(f"Error sin JSON para {format_type}: {response.content.decode()}")
    
    def test_upload_without_login(self):
        """Probar subida sin estar logueado."""
        self.client.logout()
        
        test_image = self.create_test_image(size=(50, 50))
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': test_image
        })
        
        print(f"Sin login - Status: {response.status_code}")
        
        # Debería redirigir al login o dar error 401/403
        self.assertIn(response.status_code, [302, 401, 403])
    
    def test_upload_large_file(self):
        """Probar subida de archivo grande."""
        # Crear imagen de 6MB (debería fallar)
        large_image = self.create_test_image(size=(2000, 2000))
        
        response = self.client.post('/ckeditor5/upload/', {
            'upload': large_image
        })
        
        print(f"Archivo grande - Status: {response.status_code}")
        print(f"Tamaño: {large_image.size} bytes")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                print(f"Error esperado: {error_data}")
                self.assertIn('error', error_data)
            except:
                print("Error sin JSON para archivo grande")