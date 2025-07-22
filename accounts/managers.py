from django.db import models
from django.db.models import Count, Q, Prefetch
from django.contrib.auth.models import User


class ProfileManager(models.Manager):
    """
    Optimized manager for Profile model
    """
    
    def with_user_info(self):
        """
        Get profiles with user information loaded
        """
        return self.select_related('user')
    
    def can_post_users(self):
        """
        Get profiles of users who can post
        """
        return self.with_user_info().filter(can_post=True)
    
    def pending_permissions(self):
        """
        Get profiles with pending post permission requests
        """
        return self.with_user_info().filter(
            permission_requested=True,
            can_post=False
        )
    
    def with_post_stats(self):
        """
        Annotate profiles with post statistics
        """
        return self.with_user_info().annotate(
            total_posts=Count('user__posts', distinct=True),
            published_posts=Count(
                'user__posts',
                filter=Q(user__posts__status='published'),
                distinct=True
            ),
            total_likes=Count('user__posts__likes', distinct=True),
            total_views=models.Sum('user__posts__views')
        )
    
    def active_authors(self, limit=10):
        """
        Get most active authors based on published posts
        """
        return self.with_post_stats().filter(
            can_post=True,
            published_posts__gt=0
        ).order_by('-published_posts', '-total_likes')[:limit]
    
    def with_follow_stats(self):
        """
        Annotate profiles with follower/following counts
        """
        return self.annotate(
            followers_count=Count('followed_by', distinct=True),
            following_count=Count('follows', distinct=True)
        )
    
    def popular_authors(self, limit=10):
        """
        Get popular authors based on followers and engagement
        """
        return self.with_user_info().with_follow_stats().with_post_stats().filter(
            can_post=True
        ).order_by('-followers_count', '-total_likes')[:limit]
    
    def with_follows_data(self):
        """
        Get profiles with follows and followers preloaded
        """
        return self.with_user_info().prefetch_related(
            'follows__user',
            'followed_by__user'
        )
    
    def with_recent_posts(self, limit=5):
        """
        Get profiles with recent posts preloaded
        """
        from django.db.models import Prefetch
        from posts.models import Post
        
        # Get recent published posts
        recent_posts = Post.objects.filter(
            status='published'
        ).select_related('author').order_by('-created_at')[:limit]
        
        return self.with_user_info().prefetch_related(
            Prefetch('user__posts', queryset=recent_posts)
        )
    
    def with_full_activity(self):
        """
        Get profiles with comprehensive activity data
        """
        from django.db.models import Prefetch
        from posts.models import Post, Comment
        
        # Get published posts
        published_posts = Post.objects.filter(
            status='published'
        ).select_related('author').prefetch_related('tags')
        
        # Get active comments
        active_comments = Comment.objects.filter(
            active=True
        ).select_related('post', 'post__author')
        
        return self.with_user_info().prefetch_related(
            Prefetch('user__posts', queryset=published_posts),
            Prefetch('user__comments_by_author', queryset=active_comments),
            'follows__user',
            'followed_by__user'
        ).with_follow_stats().with_post_stats()
    
    def suggested_follows(self, user, limit=10):
        """
        Get suggested profiles to follow based on common interests and connections
        """
        if not user.is_authenticated:
            return self.none()
            
        # Get IDs of users already followed
        followed_ids = user.profile.follows.values_list('user_id', flat=True)
        
        # Get IDs of users who follow the same people as the current user
        common_follows = self.filter(
            user__profile__follows__in=user.profile.follows.all()
        ).exclude(
            user=user
        ).exclude(
            user_id__in=followed_ids
        ).annotate(
            common_count=Count('user__profile__follows')
        ).order_by('-common_count')
        
        # Get IDs of users with similar post interests (based on tags)
        from django.db.models import Count
        from posts.models import Post
        
        # Get tags from posts the user has liked or commented on
        user_tags = Post.objects.filter(
            Q(likes=user) | Q(comments__author=user)
        ).values_list('tags__id', flat=True).distinct()
        
        # Find authors who write about similar topics
        similar_interests = self.filter(
            user__posts__tags__id__in=user_tags,
            user__posts__status='published'
        ).exclude(
            user=user
        ).exclude(
            user_id__in=followed_ids
        ).annotate(
            tag_match_count=Count('user__posts__tags', filter=Q(user__posts__tags__id__in=user_tags))
        ).order_by('-tag_match_count')
        
        # Combine and deduplicate results
        combined_ids = list(common_follows.values_list('id', flat=True)[:limit//2]) + \
                      list(similar_interests.values_list('id', flat=True)[:limit//2])
        
        return self.with_user_info().with_post_stats().with_follow_stats().filter(
            id__in=combined_ids
        )[:limit]


class EnhancedNotificationManager(models.Manager):
    """
    Optimized manager for Notification model
    """
    
    def with_user_info(self):
        """
        Get notifications with sender and recipient info loaded
        """
        return self.select_related(
            'recipient',
            'sender',
            'recipient__profile',
            'sender__profile'
        )
    
    def unread_for_user(self, user):
        """
        Get unread notifications for specific user
        """
        return self.with_user_info().filter(
            recipient=user,
            is_read=False
        ).order_by('-created_at')
    
    def recent_for_user(self, user, limit=20):
        """
        Get recent notifications for user (read and unread)
        """
        return self.with_user_info().filter(
            recipient=user
        ).order_by('-created_at')[:limit]
    
    def mark_as_read(self, user, notification_ids=None):
        """
        Mark notifications as read for user
        """
        queryset = self.filter(recipient=user, is_read=False)
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        return queryset.update(is_read=True)
    
    def unread_count(self, user):
        """
        Get count of unread notifications for user
        """
        return self.filter(recipient=user, is_read=False).count()
    
    def cleanup_old_read(self, days=30):
        """
        Delete old read notifications (for maintenance)
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(
            is_read=True,
            created_at__lt=cutoff_date
        ).delete()
    
    def bulk_create_notifications(self, notifications_data):
        """
        Efficiently create multiple notifications
        """
        notifications = [
            self.model(**data) for data in notifications_data
        ]
        return self.bulk_create(notifications, batch_size=100)


class UserManager(models.Manager):
    """
    Enhanced User manager with optimized queries
    """
    
    def with_profile(self):
        """
        Get users with profile information loaded
        """
        return self.select_related('profile')
    
    def authors(self):
        """
        Get users who can post (authors)
        """
        return self.with_profile().filter(profile__can_post=True)
    
    def with_post_stats(self):
        """
        Annotate users with post statistics
        """
        return self.with_profile().annotate(
            total_posts=Count('posts', distinct=True),
            published_posts=Count(
                'posts',
                filter=Q(posts__status='published'),
                distinct=True
            ),
            total_likes_received=Count('posts__likes', distinct=True),
            total_views=models.Sum('posts__views'),
            total_comments_made=Count('comments_by_author', distinct=True)
        )
    
    def top_authors(self, limit=10):
        """
        Get top authors by engagement metrics
        """
        return self.authors().with_post_stats().filter(
            published_posts__gt=0
        ).order_by('-total_likes_received', '-published_posts')[:limit]
    
    def recent_activity(self, days=7):
        """
        Get users with recent activity (posts or comments)
        """
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.with_profile().filter(
            Q(posts__created_at__gte=cutoff_date) |
            Q(comments_by_author__created_at__gte=cutoff_date)
        ).distinct()
    
    def with_posts_and_comments(self):
        """
        Get users with their posts and comments preloaded
        """
        from django.db.models import Prefetch
        from posts.models import Post, Comment
        
        # Get published posts
        published_posts = Post.objects.filter(
            status='published'
        ).select_related('author')
        
        # Get active comments
        active_comments = Comment.objects.filter(
            active=True
        ).select_related('post')
        
        return self.with_profile().prefetch_related(
            Prefetch('posts', queryset=published_posts),
            Prefetch('comments_by_author', queryset=active_comments)
        )
    
    def with_social_context(self):
        """
        Get users with their social connections preloaded
        """
        return self.with_profile().prefetch_related(
            'profile__follows',
            'profile__followed_by'
        )
    
    def with_full_context(self):
        """
        Get users with all related data preloaded for profile pages
        """
        from django.db.models import Prefetch
        from posts.models import Post, Comment
        
        # Get published posts with tags
        published_posts = Post.objects.filter(
            status='published'
        ).select_related('author').prefetch_related('tags')
        
        # Get active comments with post info
        active_comments = Comment.objects.filter(
            active=True
        ).select_related('post', 'post__author')
        
        return self.with_profile().prefetch_related(
            Prefetch('posts', queryset=published_posts),
            Prefetch('comments_by_author', queryset=active_comments),
            'profile__follows',
            'profile__followed_by',
            'notifications'
        ).annotate(
            followers_count=Count('profile__followed_by', distinct=True),
            following_count=Count('profile__follows', distinct=True)
        )
    
    def dashboard_data(self, user_id):
        """
        Get comprehensive user data for dashboard display
        """
        from django.db.models import Prefetch, Count, Sum, F, ExpressionWrapper, FloatField
        from posts.models import Post, Comment
        from django.utils import timezone
        from datetime import timedelta
        
        # Time periods for analytics
        thirty_days_ago = timezone.now() - timedelta(days=30)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Get recent posts with engagement metrics
        recent_posts = Post.objects.filter(
            author_id=user_id,
            created_at__gte=thirty_days_ago
        ).annotate(
            engagement_rate=ExpressionWrapper(
                (F('views') + Count('likes') * 5 + Count('comments') * 10) / 
                (F('views') + 1) * 100,
                output_field=FloatField()
            )
        ).order_by('-created_at')
        
        # Get recent comments on user's posts
        recent_comments = Comment.objects.filter(
            post__author_id=user_id,
            created_at__gte=thirty_days_ago,
            active=True
        ).select_related('author', 'author__profile', 'post')
        
        return self.filter(id=user_id).with_profile().prefetch_related(
            Prefetch('posts', queryset=recent_posts),
            Prefetch('posts__comments', queryset=recent_comments)
        ).annotate(
            # Overall stats
            total_posts=Count('posts', distinct=True),
            published_posts=Count('posts', filter=Q(posts__status='published'), distinct=True),
            total_views=Sum('posts__views'),
            total_likes=Count('posts__likes', distinct=True),
            total_comments=Count('posts__comments', filter=Q(posts__comments__active=True), distinct=True),
            
            # Recent activity (30 days)
            recent_posts=Count('posts', filter=Q(posts__created_at__gte=thirty_days_ago), distinct=True),
            recent_views=Sum('posts__views', filter=Q(posts__created_at__gte=thirty_days_ago)),
            recent_likes=Count('posts__likes', filter=Q(posts__created_at__gte=thirty_days_ago), distinct=True),
            recent_comments=Count('posts__comments', filter=Q(
                posts__comments__active=True,
                posts__comments__created_at__gte=thirty_days_ago
            ), distinct=True),
            
            # Very recent activity (7 days)
            weekly_posts=Count('posts', filter=Q(posts__created_at__gte=seven_days_ago), distinct=True),
            weekly_views=Sum('posts__views', filter=Q(posts__created_at__gte=seven_days_ago)),
            weekly_likes=Count('posts__likes', filter=Q(posts__created_at__gte=seven_days_ago), distinct=True),
            weekly_comments=Count('posts__comments', filter=Q(
                posts__comments__active=True,
                posts__comments__created_at__gte=seven_days_ago
            ), distinct=True),
            
            # Social stats
            followers_count=Count('profile__followed_by', distinct=True),
            following_count=Count('profile__follows', distinct=True)
        ).first()


# Note: UserManager is available but not monkey-patched to avoid conflicts
# Use User.objects for standard queries or create instances as needed