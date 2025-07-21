// Debug script for like functionality
console.log('=== LIKE SYSTEM DEBUG ===');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, checking like buttons...');
    
    // Check post like buttons
    const postLikeButtons = document.querySelectorAll('.like-button[data-slug][data-username]');
    console.log('Post like buttons found:', postLikeButtons.length);
    
    postLikeButtons.forEach((button, index) => {
        console.log(`Post button ${index}:`, {
            username: button.dataset.username,
            slug: button.dataset.slug,
            hasIcon: !!button.querySelector('i[data-feather="heart"], .like-icon'),
            hasCount: !!button.querySelector('.likes-count')
        });
    });
    
    // Check comment like buttons
    const commentLikeButtons = document.querySelectorAll('.comment-like-button[data-comment-id]');
    console.log('Comment like buttons found:', commentLikeButtons.length);
    
    commentLikeButtons.forEach((button, index) => {
        console.log(`Comment button ${index}:`, {
            commentId: button.dataset.commentId,
            hasIcon: !!button.querySelector('i[data-feather="heart"], .like-icon'),
            hasCount: !!button.querySelector('.likes-count')
        });
    });
    
    // Check if likes.js is loaded
    console.log('Body has like-initialized:', document.body.hasAttribute('data-like-initialized'));
    
    // Test click handler
    document.body.addEventListener('click', function(e) {
        if (e.target.closest('.like-button, .comment-like-button')) {
            console.log('Like button clicked:', e.target.closest('.like-button, .comment-like-button'));
        }
    });
});