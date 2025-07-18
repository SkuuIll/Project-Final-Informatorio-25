from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Post
from django.utils.text import slugify
from taggit.models import Tag


class PostModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password")
        self.post = Post.objects.create(
            author=self.user,
            title="Un Título de Prueba",
            content="Contenido de prueba.",
            status="published",
        )

    def test_post_creation(self):
        """Prueba que el post se crea correctamente y el slug se genera."""
        self.assertEqual(self.post.title, "Un Título de Prueba")
        self.assertEqual(self.post.author.username, "testuser")
        self.assertEqual(self.post.slug, slugify(self.post.title))
        self.assertEqual(str(self.post), "Un Título de Prueba")

 
class PostViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )

        self.tag_django = Tag.objects.create(name="Django")

        self.published_post = Post.objects.create(
            author=self.user,
            title="Post Publicado",
            content="Contenido publicado.",
            status="published",
        )
        self.published_post.tags.add(self.tag_django)

        self.draft_post = Post.objects.create(
            author=self.user,
            title="Post Borrador",
            content="Contenido en borrador.",
            status="draft",
        )

    def test_post_list_view(self):
        """Prueba que la lista de posts solo muestra los publicados."""
        response = self.client.get(reverse("posts:post_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_post.title)
        self.assertNotContains(response, self.draft_post.title)
        self.assertTemplateUsed(response, "posts/post_list.html")

    def test_post_detail_view(self):
        """Prueba la vista de detalle y el contador de vistas."""
        initial_views = self.published_post.views
        response = self.client.get(self.published_post.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_post.title)

        self.published_post.refresh_from_db()
        self.assertEqual(self.published_post.views, initial_views + 1)

    def test_post_create_view_logged_in(self):
        """Prueba que un usuario logueado puede acceder a la página de creación."""
        self.client.login(username="testuser", password="password")
        self.user.profile.can_post = True
        self.user.profile.save()
        response = self.client.get(reverse("posts:post_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "posts/post_form.html")

    def test_post_create_view_logged_out(self):
        """Prueba que un usuario anónimo es redirigido."""
        response = self.client.get(reverse("posts:post_create"))
        self.assertEqual(response.status_code, 302)  # Redirección
        self.assertRedirects(
            response, f"{reverse('accounts:login')}?next={reverse('posts:post_create')}"
        )

    def test_post_update_view_author(self):
        """Prueba que el autor puede editar su propio post."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(
            reverse("posts:post_update", kwargs={"slug": self.published_post.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_update_view_not_author(self):
        """Prueba que un usuario que no es el autor no puede editar."""
        self.client.login(username="otheruser", password="password")
        response = self.client.get(
            reverse("posts:post_update", kwargs={"slug": self.published_post.slug})
        )
        self.assertEqual(response.status_code, 403)  # Prohibido

    def test_like_post_view(self):
        """Prueba que un usuario puede dar like a un post."""
        self.client.login(username="testuser", password="password")
        response = self.client.post(
            reverse("posts:like_post", kwargs={"slug": self.published_post.slug})
        )
        self.assertEqual(response.status_code, 200)
        json_response = response.json()
        self.assertTrue(json_response['liked'])
        self.assertEqual(json_response['likes_count'], 1)
        self.published_post.refresh_from_db()
        self.assertTrue(self.user in self.published_post.likes.all())

    def test_post_list_by_tag_view(self):
        """Prueba que la lista de posts por etiqueta funciona correctamente."""
        post_with_other_tag = Post.objects.create(
            author=self.user,
            title="Otro Post con Etiqueta",
            content="Contenido de otro post.",
            status="published",
        )
        tag_python = Tag.objects.create(name="Python")
        post_with_other_tag.tags.add(tag_python)

        response = self.client.get(
            reverse("posts:post_list_by_tag", kwargs={"tag_slug": self.tag_django.slug})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.published_post.title)
        self.assertNotContains(response, post_with_other_tag.title)
        self.assertTemplateUsed(response, "posts/post_list.html")
