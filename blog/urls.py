from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import view_log
from .views import about, contact, collaborate, privacy, terms, cookies

urlpatterns = [
    path("admin/view_log/", view_log, name="view_log"),
    path("admin/", admin.site.urls),
    path(
        "ckeditor5/", include("django_ckeditor_5.urls"), name="ck_editor_5_upload_file"
    ),
    path("", include("posts.urls")),
    path("accounts/", include("accounts.urls")),
    path("about/", about, name="about"),
    path("contact/", contact, name="contact"),
    path("collaborate/", collaborate, name="collaborate"),
    path("privacy/", privacy, name="privacy"),
    path("terms/", terms, name="terms"),
    path("cookies/", cookies, name="cookies"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = "blog.views.custom_404"
