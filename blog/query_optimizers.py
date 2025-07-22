"""
Query optimization utilities for the DevBlog application.
Provides functions to optimize common query patterns and avoid N+1 problems.
"""
from django.db.models import Prefetch, Count, Q, F, Sum
from django.contrib.auth.models import User
from posts.models import Post, Comment
from accounts.models import Profile, Notification


def optimize_homepage_query():
    """
    Optimize the homepage query to fetch all necessary data in minimal queries.
    
    Returns:
        A queryset with all necessary data preloaded for the homepage.
    """
    # Get active comments with their authors
    active_comments = Comment.objects.filter(active=True).select_related(
        'author', 'author__profile'
    )
    
    # Get posts with all related data
    return Post.objects.filter(status='published').select_related(
        'author', 'author__profile'
    ).prefetch_related(
        Prefetch('comments', queryset=active_comments),
        'tags',
        'likes',
        'favorites'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', filter=Q(comments__active=True), distinct=True),
        favorites_count=Count('favorites', distinct=True)
    ).order_by('-is_sticky', '-created_at')


def optimize_user_profile_query(username):
    """
    Optimize the user profile query to fetch all necessary data in minimal queries.
    
    Args:
        username: The username of the user to fetch.
        
    Returns:
        A tuple containing the user object and their posts with all necessary data preloaded.
    """
    # Get the user with profile data
    user = User.objects.select_related('profile').prefetch_related(
        'profile__follows', 'profile__followed_by'
    ).annotate(
        followers_count=Count('profile__followed_by', distinct=True),
        following_count=Count('profile__follows', distinct=True),
        total_posts=Count('posts', filter=Q(posts__status='published'), distinct=True),
        total_likes=Count('posts__likes', distinct=True),
        total_views=Sum('posts__views')
    ).get(username=username)
    
    # Get the user's posts with all related data
    posts = Post.objects.filter(
        author=user, status='published'
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'comments__author__profile',
        'tags',
        'likes',
        'favorites'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', filter=Q(comments__active=True), distinct=True),
        favorites_count=Count('favorites', distinct=True)
    ).order_by('-created_at')
    
    return user, posts


def optimize_post_detail_query(username, slug):
    """
    Optimize the post detail query to fetch all necessary data in minimal queries.
    
    Args:
        username: The username of the post author.
        slug: The slug of the post.
        
    Returns:
        A tuple containing the post object and its comments with all necessary data preloaded.
    """
    # Get the post with all related data
    post = Post.objects.select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'tags',
        'likes',
        'favorites'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        favorites_count=Count('favorites', distinct=True)
    ).get(author__username=username, slug=slug)
    
    # Get the post's comments with all related data
    comments = Comment.objects.filter(
        post=post, active=True
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'likes'
    ).annotate(
        likes_count=Count('likes', distinct=True)
    ).order_by('-created_at')
    
    return post, comments


def optimize_dashboard_query(user):
    """
    Optimize the dashboard query to fetch all necessary data in minimal queries.
    
    Args:
        user: The user object.
        
    Returns:
        A dictionary containing all necessary data for the dashboard.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Time periods for analytics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Get the user with all related data
    user_data = User.objects.filter(id=user.id).select_related('profile').annotate(
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
    
    # Get recent posts
    recent_posts = Post.objects.filter(
        author=user,
        created_at__gte=thirty_days_ago
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'tags',
        'likes',
        'comments__author__profile'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', filter=Q(comments__active=True), distinct=True)
    ).order_by('-created_at')
    
    # Get unread notifications
    notifications = Notification.objects.filter(
        recipient=user,
        is_read=False
    ).select_related(
        'sender', 'sender__profile'
    ).order_by('-created_at')
    
    return {
        'user_data': user_data,
        'recent_posts': recent_posts,
        'notifications': notifications
    }


def optimize_tag_query(tag_slug):
    """
    Optimize the tag query to fetch all necessary data in minimal queries.
    
    Args:
        tag_slug: The slug of the tag.
        
    Returns:
        A queryset with all posts for the given tag with necessary data preloaded.
    """
    return Post.objects.filter(
        tags__slug=tag_slug,
        status='published'
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'tags',
        'comments__author__profile',
        'likes',
        'favorites'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', filter=Q(comments__active=True), distinct=True),
        favorites_count=Count('favorites', distinct=True)
    ).order_by('-created_at')


def optimize_search_query(query):
    """
    Optimize the search query to fetch all necessary data in minimal queries.
    
    Args:
        query: The search query string.
        
    Returns:
        A queryset with all matching posts with necessary data preloaded.
    """
    return Post.objects.filter(
        Q(title__icontains=query) | 
        Q(content__icontains=query) |
        Q(author__username__icontains=query) |
        Q(tags__name__icontains=query),
        status='published'
    ).select_related(
        'author', 'author__profile'
    ).prefetch_related(
        'tags',
        'comments__author__profile',
        'likes',
        'favorites'
    ).annotate(
        likes_count=Count('likes', distinct=True),
        comments_count=Count('comments', filter=Q(comments__active=True), distinct=True),
        favorites_count=Count('favorites', distinct=True)
    ).distinct().order_by('-created_at')