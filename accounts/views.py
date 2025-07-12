from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import transaction
from .models import Profile, Notification
from django.contrib.auth.views import LoginView
from django.contrib.admin.views.decorators import staff_member_required
from .forms import UserUpdateForm, ProfileUpdateForm, CustomUserCreationForm, LoginForm
import os
from django.conf import settings
from django.urls import reverse


class CustomLoginView(LoginView):
    """
    Vista de inicio de sesión personalizada que especifica la ubicación de la plantilla.
    """

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
    # Notificar a todos los administradores
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
        # Crear notificación
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            message=f'{request.user.username} ha comenzado a seguirte.',
            link=reverse('accounts:profile_by_pk', kwargs={'pk': request.user.pk})
        )
    return redirect("accounts:profile_by_pk", pk=pk)


@login_required
def unfollow_user(request, pk):
    user_to_unfollow = get_object_or_404(User, pk=pk)
    request.user.profile.follows.remove(user_to_unfollow.profile)
    return redirect("accounts:profile_by_pk", pk=pk)


@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    # Marcar todas las notificaciones como leídas al ver la lista
    request.user.notifications.update(is_read=True)
    return render(request, 'accounts/notification_list.html', {'notifications': notifications})


@login_required
def profile_view(request, pk=None):
    if pk:
        user = get_object_or_404(User, pk=pk)
        is_own_profile = request.user == user
    else:
        user = request.user
        is_own_profile = True

    profile, created = Profile.objects.get_or_create(user=user)

    context = {"user": user, "profile": profile, "is_own_profile": is_own_profile}
    return render(request, "accounts/profile.html", context)


@login_required
@transaction.atomic
def profile_edit(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "¡Tu perfil ha sido actualizado exitosamente!")
            return redirect("accounts:profile")
        else:
            messages.error(request, "Por favor, corrige los errores a continuación.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    context = {"user_form": user_form, "profile_form": profile_form}
    return render(request, "accounts/profile_edit.html", context)


def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, "¡Tu cuenta ha sido creada! Ya puedes iniciar sesión."
            )
            return redirect("accounts:login")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})


@staff_member_required
def view_log(request):
    log_file_path = os.path.join(settings.BASE_DIR, "logs", "admin.log")
    try:
        with open(log_file_path, "r") as f:
            log_content = f.read()
    except FileNotFoundError:
        log_content = "El archivo de log no se encuentra."
    return render(request, "admin/log_viewer.html", {"log_content": log_content})
