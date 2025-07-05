from django.urls import path
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    dashboard_view,
    register,
)

app_name = 'posts'

urlpatterns = [
    path('', PostListView.as_view(), name='post_list'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('register/', register, name='register'),
    path('post/nuevo/', PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/', PostDetailView.as_view(), name='post_detail'),
    path('post/<slug:slug>/editar/', PostUpdateView.as_view(), name='post_update'),
    path('post/<slug:slug>/eliminar/', PostDeleteView.as_view(), name='post_delete'),
]
