from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from .models import Notification
from django.contrib.auth.views import LoginView
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.admin.views.decorators import staff_member_required
from .forms import UserUpdateForm, ProfileUpdateForm, CustomUserCreationForm, LoginForm
import os
from django.conf import settings
from django.urls import reverse, reverse_lazy


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"

User = get_user_model()

@login_required
def delete_notifications(request):
    request.user.notifications.all().delete()
    messages.success(request, "Todas las notificaciones han sido eliminadas.")
    return redirect("accounts:notification_list")

@login_required
def request_post_permission(request):
    admins = User.objects.filter(is_staff=True)
    for admin in admins:
        Notification.objects.create(
            recipient=admin,
            sender=request.user,
            message=f'El usuario {request.user.username} solicita permiso para postear.',
            link=reverse('admin:accounts_profile_change', args=[request.user.profile.pk])
        )
    messages.success(request, "Tu solicitud ha sido enviada a los administradores.")
    return redirect("posts:dashboard")

@login_required
def follow_user(request, pk):
    user_to_follow = get_object_or_404(User, pk=pk)
    if user_to_follow != request.user:
        request.user.profile.follows.add(user_to_follow.profile)
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            message=f'{request.user.username} ha comenzado a seguirte.',
            link=reverse('accounts:profile', kwargs={'pk': request.user.pk})
        )
    return redirect("accounts:profile", pk=pk)

@login_required
def unfollow_user(request, pk):
    user_to_unfollow = get_object_or_404(User, pk=pk)
    request.user.profile.follows.remove(user_to_unfollow.profile)
    return redirect("accounts:profile", pk=pk)

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    request.user.notifications.update(is_read=True)
    return render(request, 'accounts/notification_list.html', {'notifications': notifications})


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/profile.html"
    context_object_name = "profile_user" 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = self.request.user == self.object
        return context


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        messages.success(self.request, "¡Tu cuenta ha sido creada! Ya puedes iniciar sesión.")
        return super().form_valid(form)

@staff_member_required
def view_log(request):
    log_file_path = os.path.join(settings.BASE_DIR, "logs", "admin.log")
    try:
        with open(log_file_path, "r") as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = "El archivo de log no se encuentra."
    return render(request, "admin/log_viewer.html", {"log_content": log_content})

@login_required
def settings_view(request):
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "¡Tu perfil ha sido actualizado exitosamente!")
                return redirect('accounts:settings')
        elif 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                return JsonResponse({'success': True, 'message': '¡Contraseña cambiada con éxito!'})
            else:
                return JsonResponse({'success': False, 'errors': password_form.errors}, status=400)
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        password_form = PasswordChangeForm(request.user)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'accounts/settings.html', context)