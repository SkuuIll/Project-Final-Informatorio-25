from django.contrib.syndication.views import Feed
from django.urls import reverse
from .models import Post


class LatestPostsFeed(Feed):
    title = "DevBlog - Últimos Posts"
    link = "/feed/"
    description = "Los últimos artículos publicados en DevBlog."

    def items(self):
        return Post.objects.order_by("-created_at")[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.content

    def item_link(self, item):
        return reverse("posts:post_detail", args=[item.slug])
