from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Post, Comment
from accounts.models import Notification
import os

@receiver(post_delete, sender=Post)
def delete_post_header_image(sender, instance, **kwargs):
    if instance.header_image:
        if os.path.isfile(instance.header_image.path):
            os.remove(instance.header_image.path)

@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created:
        post_author = instance.post.author
        comment_author = instance.author

        if post_author != comment_author:
            Notification.objects.create(
                recipient=post_author,
                sender=comment_author,
                message=f'{comment_author.username} ha comentado en tu post "{instance.post.title}".',
                link=instance.post.get_absolute_url()
            )
