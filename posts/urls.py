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
    favorite_post,
    favorite_list,
    SearchResultsView,
    PostViewSet,
    CommentDeleteView,
    PostListByTagView,
)

app_name = "posts"

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post-api")

urlpatterns = [
    path("", PostListView.as_view(), name="post_list"),
    path("tag/<str:tag_slug>/", PostListByTagView.as_view(), name="post_list_by_tag"),
    path("api/", include(router.urls)),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("favoritos/", favorite_list, name="favorite_list"),
    path("post/nuevo/", PostCreateView.as_view(), name="post_create"),
    path("post/<slug:slug>/", PostDetailView.as_view(), name="post_detail"),
    path("post/<slug:slug>/editar/", PostUpdateView.as_view(), name="post_update"),
    path("post/<slug:slug>/eliminar/", PostDeleteView.as_view(), name="post_delete"),
    path("post/<slug:slug>/like/", like_post, name="like_post"),
    path("post/<slug:slug>/favorite/", favorite_post, name="favorite_post"),
    path(
        "comment/<int:pk>/delete/", CommentDeleteView.as_view(), name="comment_delete"
    ),
    path("search/", SearchResultsView.as_view(), name="search_results"),
    path("feed/", LatestPostsFeed(), name="post_feed"),
]
