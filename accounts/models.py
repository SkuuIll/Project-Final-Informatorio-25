from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .managers import ProfileManager, EnhancedNotificationManager


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="Avatar"
    )
    
    # Managers
    objects = models.Manager()  # Default manager
    optimized = ProfileManager()  # Optimized manager
    bio = models.TextField(max_length=500, blank=True, verbose_name="Biografía")
    can_post = models.BooleanField(default=False, verbose_name="Puede postear")
    permission_requested = models.BooleanField(default=False, verbose_name="Permiso solicitado")
    follows = models.ManyToManyField(
        'self',
        related_name='followed_by',
        symmetrical=False,
        blank=True,
        verbose_name="Sigue a"
    )

    def __str__(self):
        return self.user.username
        
    class Meta:
        indexes = [
            # Core profile queries
            models.Index(fields=['user'], name='profile_user'),
            models.Index(fields=['can_post'], name='profile_can_post'),
            models.Index(fields=['permission_requested'], name='profile_permission_req'),
            
            # Permission management
            models.Index(fields=['can_post', 'permission_requested'], name='profile_permissions'),
            models.Index(fields=['permission_requested', 'can_post'], name='profile_pending_perms'),
        ]


class Notification(models.Model):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_notifications"
    )
    
    # Managers
    objects = models.Manager()  # Default manager
    optimized = EnhancedNotificationManager()  # Optimized manager
    message = models.CharField(max_length=255)
    link = models.URLField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            # Core notification queries
            models.Index(fields=['recipient', '-created_at'], name='notif_recipient_recent'),
            models.Index(fields=['recipient', 'is_read'], name='notif_recipient_read'),
            models.Index(fields=['sender', '-created_at'], name='notif_sender_recent'),
            
            # Unread notifications (most common query)
            models.Index(fields=['recipient', 'is_read', '-created_at'], name='notif_unread_recent'),
            
            # Cleanup queries
            models.Index(fields=['is_read', 'created_at'], name='notif_cleanup'),
            models.Index(fields=['created_at'], name='notif_created_at'),
        ]


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
