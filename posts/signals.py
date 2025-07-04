from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Comment

@receiver(post_save, sender=Comment)
def notify_author_on_comment(sender, instance, created, **kwargs):
    if created:
        post = instance.post
        author = post.author
        print(f"Nuevo comentario en tu post '{post.title}' por {instance.author.username}")