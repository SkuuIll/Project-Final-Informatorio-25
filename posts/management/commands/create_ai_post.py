
import os
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from posts.models import Post
from posts.ai_generator import (
    extract_content_from_url,
    rewrite_content_with_ai,
    generate_tags_with_ai,
)
from dotenv import load_dotenv

load_dotenv()  

class Command(BaseCommand):
    help = 'Crea un nuevo post a partir de una URL usando IA para reescribir el contenido.'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='La URL del artículo original.')
        parser.add_argument('--author_id', type=int, help='El ID del usuario que será el autor del post.')

    def handle(self, *args, **options):
        url = options['url']
        author_id = options['author_id']

        if not url:
            raise CommandError('La URL es obligatoria. Usa --url <URL>')
        if not author_id:
            raise CommandError('El ID del autor es obligatorio. Usa --author_id <ID>')

        User = get_user_model()
        try:
            author = User.objects.get(pk=author_id)
        except User.DoesNotExist:
            raise CommandError(f'El usuario con ID "{author_id}" no existe.')

        self.stdout.write(self.style.NOTICE(f'Procesando URL: {url}'))

        self.stdout.write('Extrayendo contenido del artículo original...')
        original_content = extract_content_from_url(url)
        if not original_content:
            raise CommandError('No se pudo extraer contenido de la URL.')

        self.stdout.write(self.style.NOTICE('Usando IA para reescribir el contenido y generar un título...'))
        title, new_content = rewrite_content_with_ai(original_content)

        self.stdout.write(self.style.NOTICE('Generando tags con IA...'))
        tags = generate_tags_with_ai(new_content)

        self.stdout.write(self.style.SUCCESS('Creando el post en la base de datos...'))
        
        new_post = Post.objects.create(
            author=author,
            title=title,
            content=new_content,
            status='published', 
        )

        if tags:
            new_post.tags.add(*tags)
        
        new_post.save()

        self.stdout.write(self.style.SUCCESS(
            f'¡Post creado con éxito! ID: {new_post.id}, Título: "{new_post.title}"'
        ))
