from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction
from .models import Profile
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from .forms import UserUpdateForm, ProfileUpdateForm, CustomUserCreationForm, LoginForm
import os
from django.conf import settings

class CustomLoginView(LoginView):
    """
    Vista de inicio de sesión personalizada que especifica la ubicación de la plantilla.
    """
    form_class = LoginForm
    template_name = 'accounts/login.html'

User = get_user_model()

@login_required
def profile_view(request, pk=None):
    if pk:
        user = get_object_or_404(User, pk=pk)
        is_own_profile = (request.user == user)
    else:
        user = request.user
        is_own_profile = True
    
    profile, created = Profile.objects.get_or_create(user=user)
    
    context = {
        'user': user,
        'profile': profile,
        'is_own_profile': is_own_profile
    }
    return render(request, 'accounts/profile.html', context)

@login_required
@transaction.atomic
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, '¡Tu perfil ha sido actualizado exitosamente!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Por favor, corrige los errores a continuación.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'accounts/profile_edit.html', context)

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Tu cuenta ha sido creada! Ya puedes iniciar sesión.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@staff_member_required
def view_log(request):
    log_file_path = os.path.join(settings.BASE_DIR, 'logs', 'admin.log')
    try:
        with open(log_file_path, 'r') as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = "El archivo de log no se encuentra."
    return render(request, 'admin/log_viewer.html', {'log_content': log_content})

