from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import CustomLoginView, profile_view, profile_edit, register

app_name = 'accounts'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('register/', register, name='register'),
    path('profile/', profile_view, name='profile'),
    path('profile/<int:pk>/', profile_view, name='profile_by_pk'),
    path('profile/edit/', profile_edit, name='profile_edit'),
    
    path('password_change/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html', 
        success_url=reverse_lazy('accounts:password_change_done') 
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'
    ), name='password_change_done'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset_form.html',
        email_template_name='accounts/password_reset_email.html', 
        subject_template_name='accounts/password_reset_subject.txt', 
        success_url=reverse_lazy('accounts:password_reset_done')
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url=reverse_lazy('accounts:password_reset_complete')
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),

    path('', include('django.contrib.auth.urls')),
]
