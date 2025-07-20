from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Profile


class ProfileCreationTest(TestCase):
    def test_profile_is_created_on_user_creation(self):
        """Prueba que se crea un Profile automáticamente cuando se crea un User."""
        user = User.objects.create_user(username="newuser", password="password")
        self.assertIsNotNone(user.profile)
        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(user.profile.user, user)


class AccountsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        # El profile se crea automáticamente por el signal

    def test_register_view(self):
        """Prueba la vista de registro de un nuevo usuario."""
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)

        # Prueba el envío de datos válidos
        new_user_data = {
            "username": "anotheruser",
            "email": "another@test.com",
            "password1": "a-very-valid-password-123!",
            "password2": "a-very-valid-password-123!",
            "cf-turnstile-response": "cf-chl-widget-xxxxxxxxxxxxx",  # Simular CAPTCHA válido
        }
        response = self.client.post(reverse("accounts:register"), new_user_data)
        self.assertEqual(response.status_code, 302)  # Redirección al login
        self.assertTrue(User.objects.filter(username="anotheruser").exists())

    def test_register_view_password_mismatch(self):
        """Prueba el registro con contraseñas que no coinciden."""
        new_user_data = {
            "username": "userwithbadpass",
            "email": "badpass@test.com",
            "password1": "a-very-valid-password-123!",
            "password2": "a-different-password",
            "cf-turnstile-response": "cf-chl-widget-xxxxxxxxxxxxx",
        }
        response = self.client.post(reverse("accounts:register"), new_user_data)
        self.assertEqual(response.status_code, 200) # Debería volver a mostrar el formulario
        # El mensaje de error exacto puede depender de tu formulario.
        self.assertContains(response, "Los dos campos de contraseñas no coinciden entre si.")
        self.assertFalse(User.objects.filter(username="userwithbadpass").exists())

    def test_profile_view_logged_in(self):
        """Prueba que un usuario logueado puede ver su perfil."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("accounts:profile", kwargs={"pk": self.user.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")
        self.assertContains(response, self.user.username)

    def test_profile_view_logged_out(self):
        """Prueba que un usuario anónimo es redirigido desde la vista de perfil."""
        profile_url = reverse("accounts:profile", kwargs={"pk": self.user.pk})
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={profile_url}")


    def test_profile_edit_view(self):
        """Prueba que un usuario puede editar su perfil."""
        self.client.login(username="testuser", password="password")
        response = self.client.get(reverse("accounts:profile_edit"))
        self.assertEqual(response.status_code, 200)

        # Prueba el envío de datos para actualizar
        updated_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": self.user.email,
            "bio": "Esta es una nueva biografía.",
        }
        response = self.client.post(reverse("accounts:profile_edit"), updated_data)
        self.assertEqual(response.status_code, 302)  # Redirección al perfil
        self.assertRedirects(response, reverse("accounts:profile", kwargs={"pk": self.user.pk}))

        # Refrescar datos desde la BD
        self.user.refresh_from_db()
        self.user.profile.refresh_from_db()

        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.profile.bio, "Esta es una nueva biografía.")