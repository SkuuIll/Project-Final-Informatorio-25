from django.contrib import admin
from .models import Post, Comment


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para los Posts."""

    list_display = ("title", "author", "status", "created_at", "views", "is_sticky")
    list_filter = ("status", "created_at", "author", "is_sticky")
    search_fields = ("title", "body")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"
    ordering = ("status", "created_at")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para los Comentarios."""

    list_display = ("author", "post", "created_at", "active")
    list_filter = ("active", "created_at")
    search_fields = ("author__username", "body")
    actions = ["approve_comments"]

    def approve_comments(self, request, queryset):
        queryset.update(active=True)

    approve_comments.short_description = "Aprobar comentarios seleccionados"
