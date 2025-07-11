from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm, AuthenticationForm
from turnstile.fields import TurnstileField

class LoginForm(AuthenticationForm):
    captcha = TurnstileField()

class CustomUserCreationForm(UserCreationForm):
    captcha = TurnstileField()
    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email',)

class UserUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar los datos básicos del usuario (nombre, apellido, email).
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    """
    Formulario para actualizar el avatar del perfil con validación de tamaño.
    """
    class Meta:
        model = Profile
        fields = ['avatar', 'bio']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-violet-50 dark:file:bg-slate-700 file:text-violet-700 dark:file:text-slate-200 hover:file:bg-violet-100 dark:hover:file:bg-slate-600'
            })
        }

    def clean_avatar(self):
        """
        Valida que el tamaño del archivo del avatar no exceda los 2MB.
        """
        avatar = self.cleaned_data.get('avatar', False)
        if avatar:
            if avatar.size > 2 * 1024 * 1024:  # 2MB
                raise forms.ValidationError("¡El tamaño de la imagen no puede ser mayor a 2MB!")
        return avatar

class CustomPasswordChangeForm(PasswordChangeForm):
    """
    Formulario personalizado para cambiar la contraseña para que coincida con el estilo.
    Lo dejamos aquí por si lo necesitas en el futuro.
    """
    pass
