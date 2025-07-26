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
    api_existing_images,
)
from .ai_views import (
    ai_post_generator_view,
    ai_post_generator_simple_view,
    AIPostGeneratorStreamView,
)
# from .views.image_views import (
#     image_gallery_view,
#     api_get_images,
#     api_validate_image,
#     image_selector_modal,
#     image_preview,
# )
# from .prompt_views import (
#     prompt_list_view,
#     prompt_create_view,
#     prompt_edit_view,
#     prompt_delete_view,
#     prompt_set_default_view,
#     prompt_preview_view,
#     prompt_ajax_get,
#     prompt_duplicate_view,
# )

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
    path('generate-ai-post-stream/', AIPostGeneratorStreamView.as_view(), name='ai_post_generator_stream'),
    path('admin/api/existing-images/', api_existing_images, name='api_existing_images'),
    
    # URLs para gestión de prompts (comentadas temporalmente)
    # path('admin/prompts/', prompt_list_view, name='prompt_list'),
    # path('admin/prompts/create/', prompt_create_view, name='prompt_create'),
    # path('admin/prompts/<int:prompt_id>/edit/', prompt_edit_view, name='prompt_edit'),
    # path('admin/prompts/<int:prompt_id>/delete/', prompt_delete_view, name='prompt_delete'),
    # path('admin/prompts/<int:prompt_id>/set-default/', prompt_set_default_view, name='prompt_set_default'),
    # path('admin/prompts/<int:prompt_id>/duplicate/', prompt_duplicate_view, name='prompt_duplicate'),
    # path('admin/prompts/preview/', prompt_preview_view, name='prompt_preview'),
    # path('admin/prompts/ajax/<int:prompt_id>/', prompt_ajax_get, name='prompt_ajax_get'),
    
    # URLs para gestión de imágenes (comentadas temporalmente)
    # path('images/', image_gallery_view, name='image_gallery'),
    # path('api/images/', api_get_images, name='api_get_images'),
    # path('api/validate-image/', api_validate_image, name='api_validate_image'),
    # path('image-selector-modal/', image_selector_modal, name='image_selector_modal'),
    # path('image-preview/<path:image_path>/', image_preview, name='image_preview'),
]