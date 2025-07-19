from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from .models import Post, Comment, AIModel
from .forms import AiPostGeneratorForm, AIModelForm
from .ai_generator import (
    generate_complete_post,
)
from .forms import COMPLETE_POST_PROMPT

class AIModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    actions = ['activate_model']

    def activate_model(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(request, "Solo puedes activar un modelo a la vez.", level=messages.ERROR)
            return
        model = queryset.first()
        model.is_active = True
        model.save()
        self.message_user(request, f"El modelo {model.name} ha sido activado.", level=messages.SUCCESS)

    activate_model.short_description = "Activar modelo seleccionado"

admin.site.register(AIModel, AIModelAdmin)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """Configuración del panel de administración para los Posts."""
    list_display = ("title", "author", "status", "created_at", "views", "is_sticky")
    list_filter = ("status", "created_at", "author", "is_sticky")
    search_fields = ("title", "content")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    change_list_template = "admin/posts/post/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "generate-ai/",
                self.admin_site.admin_view(self.generate_ai_post_view),
                name="post_generate_ai",
            ),
        ]
        return custom_urls + urls

    def generate_ai_post_view(self, request):
        if request.method == "POST":
            form = AiPostGeneratorForm(request.POST)
            if form.is_valid():
                url = form.cleaned_data['url']
                rewrite_prompt = form.cleaned_data['rewrite_prompt']
                tag_prompt = form.cleaned_data['tag_prompt']
                extract_images = form.cleaned_data.get('extract_images', True)
                max_images = form.cleaned_data.get('max_images', 5)

                try:
                    result = generate_complete_post(url, rewrite_prompt, extract_images=extract_images, max_images=max_images)
                    if not result.get('success'):
                        self.message_user(request, f"No se pudo generar el post: {result.get('error', 'Error desconocido')}", level=messages.ERROR)
                        return redirect(".")

                    title = result.get('title', 'Título no generado')
                    content = result.get('content', '')
                    tags = result.get('tags', [])

                    post = Post.objects.create(
                        author=request.user,
                        title=title,
                        content=content,
                        status='draft',
                    )
                    if tags:
                        post.tags.add(*tags)

                    self.message_user(request, f"Post generado con éxito como borrador. Ya puedes editarlo.", level=messages.SUCCESS)
                    return redirect("admin:posts_post_change", post.id)

                except Exception as e:
                    self.message_user(request, f"Ocurrió un error: {e}", level=messages.ERROR)
                    return redirect(".")
        else:
            form = AiPostGeneratorForm()

        context = dict(
           self.admin_site.each_context(request),
           form=form,
           title="Generar Post con IA",
        )
        return render(request, "admin/posts/post/ai_generator.html", context)


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
