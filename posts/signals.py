from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Post, Comment


@receiver(post_save, sender=Comment)
def update_post_comment_count(sender, instance, created, **kwargs):
    """
    Actualiza el contador de comentarios en caché cuando se crea o actualiza un comentario.
    """
    if instance.post:
        post = instance.post
        post.cached_comments_count = post.comments.filter(active=True).count()
        post.save(update_fields=['cached_comments_count', 'last_activity'])


@receiver(post_delete, sender=Comment)
def update_post_comment_count_on_delete(sender, instance, **kwargs):
    """
    Actualiza el contador de comentarios en caché cuando se elimina un comentario.
    """
    if instance.post:
        post = instance.post
        post.cached_comments_count = post.comments.filter(active=True).count()
        post.save(update_fields=['cached_comments_count', 'last_activity'])


@receiver(m2m_changed, sender=Post.likes.through)
def update_post_likes_count(sender, instance, action, **kwargs):
    """
    Actualiza el contador de likes en caché cuando cambia la relación many-to-many.
    """
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.cached_likes_count = instance.likes.count()
        instance.save(update_fields=['cached_likes_count', 'last_activity'])


@receiver(m2m_changed, sender=Comment.likes.through)
def update_comment_likes_count(sender, instance, action, **kwargs):
    """
    Actualiza el contador de likes en caché para el comentario y actualiza la última actividad del post.
    """
    if action in ['post_add', 'post_remove', 'post_clear'] and instance.post:
        # Aquí podríamos agregar un campo cached_likes_count al modelo Comment si fuera necesario
        instance.post.last_activity = instance.created_at
        instance.post.save(update_fields=['last_activity'])