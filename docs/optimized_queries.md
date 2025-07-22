# Optimized Query Guide

This document provides guidance on using the optimized model managers and query utilities to avoid N+1 query problems and improve application performance.

## What are N+1 Query Problems?

The N+1 query problem occurs when your code:
1. Executes 1 query to retrieve a list of N objects
2. Then executes N additional queries to retrieve related data for each object

This results in N+1 total queries, which can severely impact performance as N grows.

## Using Optimized Model Managers

### Post Manager

The `PostManager` provides optimized methods for common post-related queries:

```python
# Get published posts with all relations loaded
posts = Post.optimized.published_with_relations()

# Get posts with counts of likes, comments, etc.
posts = Post.optimized.with_counts()

# Get popular posts
popular_posts = Post.optimized.popular()

# Get posts by tag
tag_posts = Post.optimized.by_tag('python')

# Get posts for homepage feed with all necessary data
homepage_posts = Post.optimized.homepage_feed()

# Get posts for user feed based on followed authors
user_feed = Post.optimized.user_feed(request.user)
```

### Comment Manager

The `CommentManager` provides optimized methods for comment-related queries:

```python
# Get active comments with author information
comments = Comment.optimized.active().with_author()

# Get comments for a specific post
post_comments = Comment.optimized.for_post(post)

# Get comments with like counts
comments = Comment.optimized.with_likes()

# Get comments with post information
comments = Comment.optimized.with_post_info()

# Get recent comments with full context
recent_comments = Comment.optimized.recent_with_context()

# Get comments with user like status
comments = Comment.optimized.with_user_like_status(request.user)
```

### User Manager

The `UserManager` provides optimized methods for user-related queries:

```python
# Get users with profile information
users = User.optimized.with_profile()

# Get users who can post (authors)
authors = User.optimized.authors()

# Get users with post statistics
users = User.optimized.with_post_stats()

# Get top authors
top_authors = User.optimized.top_authors()

# Get users with recent activity
active_users = User.optimized.recent_activity()

# Get users with posts and comments preloaded
users = User.optimized.with_posts_and_comments()

# Get users with social context
users = User.optimized.with_social_context()

# Get comprehensive dashboard data for a user
user_data = User.optimized.dashboard_data(user_id)
```

### Profile Manager

The `ProfileManager` provides optimized methods for profile-related queries:

```python
# Get profiles with user information
profiles = Profile.optimized.with_user_info()

# Get profiles of users who can post
can_post_profiles = Profile.optimized.can_post_users()

# Get profiles with pending permission requests
pending_profiles = Profile.optimized.pending_permissions()

# Get profiles with post statistics
profiles = Profile.optimized.with_post_stats()

# Get most active authors
active_authors = Profile.optimized.active_authors()

# Get profiles with follower/following counts
profiles = Profile.optimized.with_follow_stats()

# Get popular authors
popular_authors = Profile.optimized.popular_authors()

# Get suggested profiles to follow
suggested_profiles = Profile.optimized.suggested_follows(request.user)
```

## Query Optimization Utilities

The `query_optimizers.py` module provides functions for optimizing complex queries:

```python
from blog.query_optimizers import (
    optimize_homepage_query,
    optimize_user_profile_query,
    optimize_post_detail_query,
    optimize_dashboard_query,
    optimize_tag_query,
    optimize_search_query
)

# Get optimized homepage data
homepage_posts = optimize_homepage_query()

# Get optimized user profile data
user, user_posts = optimize_user_profile_query(username)

# Get optimized post detail data
post, comments = optimize_post_detail_query(username, slug)

# Get optimized dashboard data
dashboard_data = optimize_dashboard_query(request.user)

# Get optimized tag search results
tag_posts = optimize_tag_query(tag_slug)

# Get optimized search results
search_results = optimize_search_query(query)
```

## Best Practices

1. **Use the optimized managers**: Always use the optimized managers (`Post.optimized`, `Comment.optimized`, etc.) instead of the default managers when fetching related data.

2. **Prefer existing methods**: Use the provided methods whenever possible instead of creating custom queries.

3. **Check the query count**: Use Django Debug Toolbar to monitor the number of queries executed by your views.

4. **Batch process related objects**: When processing related objects, use prefetch_related to load them in a single query.

5. **Use select_related for foreign keys**: Always use select_related for foreign key relationships.

6. **Use prefetch_related for reverse relations and many-to-many**: Use prefetch_related for reverse foreign keys and many-to-many relationships.

7. **Annotate counts instead of len()**: Use annotate with Count() instead of calling len() on querysets.

8. **Avoid filtering in Python**: Filter in the database query rather than in Python code.

## Example View Implementation

Here's an example of how to use these optimized queries in a view:

```python
def homepage_view(request):
    # Get optimized homepage data
    posts = Post.optimized.homepage_feed()
    
    # Get popular authors
    popular_authors = Profile.optimized.popular_authors(limit=5)
    
    return render(request, 'homepage.html', {
        'posts': posts,
        'popular_authors': popular_authors
    })

def post_detail_view(request, username, slug):
    # Get optimized post detail data
    post, comments = optimize_post_detail_query(username, slug)
    
    # Get related posts
    related_posts = Post.optimized.with_related_posts()(post)
    
    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'related_posts': related_posts
    })
```