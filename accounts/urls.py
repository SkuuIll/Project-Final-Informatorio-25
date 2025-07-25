from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    CustomLoginView,
    ProfileView,
    settings_view,
    RegisterView,
    notification_list,
    follow_user,
    unfollow_user,
    request_post_permission,
    delete_notifications,
)
from .axes_views import locked_out, reset_lockout_view as unlock_user

app_name = "accounts"

from blog.decorators import sensitive_post_limit

urlpatterns = [
    path("login/", sensitive_post_limit(group='login', rate='5/m')(CustomLoginView.as_view()), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("@<str:username>/", ProfileView.as_view(), name="profile"),
    path("settings/", settings_view, name="settings"),
    path("notifications/", notification_list, name="notification_list"),
    path("notifications/delete/", delete_notifications, name="delete_notifications"),
    path("follow/<str:username>/", follow_user, name="follow_user"),
    path("unfollow/<str:username>/", unfollow_user, name="unfollow_user"),
    path("request-permission/", request_post_permission, name="request_post_permission"),
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url=reverse_lazy("accounts:password_change_done"),
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset_form.html",
            email_template_name="accounts/password_reset_email.html",
            subject_template_name="accounts/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path("", include("django.contrib.auth.urls")),
    
    # Django-axes URLs
    path("locked/", locked_out, name="locked_out"),
    path("unlock/<str:username>/", unlock_user, name="unlock_user"),
]
