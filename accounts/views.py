from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib import messages
from django.http import JsonResponse
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
from blog.decorators import sensitive_post_limit, user_action_limit
from blog.ratelimit import get_client_ip
import logging
from django.utils.decorators import method_decorator

logger = logging.getLogger('django.security')


class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    
    @method_decorator(sensitive_post_limit(group='login', rate='5/m'))
    def post(self, request, *args, **kwargs):
        # Registrar intento de inicio de sesión
        ip = get_client_ip(request)
        username = request.POST.get('username', '')
        logger.info(
            f"Intento de inicio de sesión: usuario={username}, ip={ip}",
            extra={
                'username': username,
                'ip': ip,
                'path': request.path,
            }
        )
        return super().post(request, *args, **kwargs)

User = get_user_model()

@login_required
def delete_notifications(request):
    request.user.notifications.all().delete()
    messages.success(request, "Todas las notificaciones han sido eliminadas.")
    return redirect("accounts:notification_list")

@login_required
def request_post_permission(request):
    if not request.user.profile.permission_requested:
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                recipient=admin,
                sender=request.user,
                message=f'El usuario {request.user.username} solicita permiso para postear.',
                link=reverse('admin:accounts_profile_change', args=[request.user.profile.pk])
            )
        request.user.profile.permission_requested = True
        request.user.profile.save()
        messages.success(request, "Tu solicitud ha sido enviada a los administradores.")
    else:
        messages.warning(request, "Ya has enviado una solicitud de permiso.")
    return redirect("posts:dashboard")

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow != request.user:
        request.user.profile.follows.add(user_to_follow.profile)
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            message=f'{request.user.username} ha comenzado a seguirte.',
            link=reverse('accounts:profile', kwargs={'username': request.user.username})
        )
    return redirect("accounts:profile", username=user_to_follow.username)

@login_required
def unfollow_user(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    request.user.profile.follows.remove(user_to_unfollow.profile)
    return redirect("accounts:profile", username=user_to_unfollow.username)

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    request.user.notifications.update(is_read=True)
    return render(request, 'accounts/notification_list.html', {'notifications': notifications})


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/profile.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        return get_object_or_404(User, username=self.kwargs.get('username'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_own_profile'] = self.request.user == self.object
        context['is_following'] = self.request.user.profile.follows.filter(user=self.object).exists()
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
    user_form = UserUpdateForm(instance=request.user)
    profile_form = ProfileUpdateForm(instance=request.user.profile)
    password_form = PasswordChangeForm(request.user)

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
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'accounts/settings.html', context)