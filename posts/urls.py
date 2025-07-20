from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .feeds import LatestPostsFeed
from .views import (
    PostListView,
    PostDetailView,
    PostCreateView,
    PostUpdateView,
    PostDeleteView,
    dashboard_view,
    like_post,
    like_comment,
    favorite_post,
    favorite_list,
    SearchResultsView,
    PostViewSet,
    CommentDeleteView,
    PostListByTagView,
    TagListView,
    PostArchiveView,
    upload_image_view,
    ai_post_generator_view,
    ai_post_generator_simple_view,
)

app_name = "posts"

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post-api")

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("tags/", TagListView.as_view(), name="tag_list"),
    path("tag/<str:tag_slug>/", PostListByTagView.as_view(), name="post_list_by_tag"),
    path("api/", include(router.urls)),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("favoritos/", favorite_list, name="favorite_list"),
    path("post/nuevo/", PostCreateView.as_view(), name="post_create"),
    path("post/<str:username>/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    path("post/<str:username>/<slug:slug>/editar/", PostUpdateView.as_view(), name="post_update"),
    path("post/<str:username>/<slug:slug>/eliminar/", PostDeleteView.as_view(), name="post_delete"),
    path("post/<str:username>/<slug:slug>/like/", like_post, name="like_post"),
    path("post/<str:username>/<slug:slug>/favorite/", favorite_post, name="favorite_post"),
    path("comment/<int:pk>/like/", like_comment, name="like_comment"),
    path(
        "comment/<int:pk>/delete/", CommentDeleteView.as_view(), name="comment_delete"
    ),
    path("search/", SearchResultsView.as_view(), name="search_results"),
    path("feed/", LatestPostsFeed(), name="post_feed"),
    path("archive/", PostArchiveView.as_view(), name="archive_list"),
    path("upload-image/", upload_image_view, name="ckeditor_upload_image"),
    
    path('generate-ai-post/', ai_post_generator_view, name='ai_post_generator'),
    path('generate-ai-post-simple/', ai_post_generator_simple_view, name='ai_post_generator_simple'),
]