// Simple test script for like functionality
console.log('=== TESTING LIKE FUNCTIONALITY ===');

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, testing like buttons...');
    
    // Test post like buttons
    const postButtons = document.querySelectorAll('.like-button[data-slug][data-username]');
    console.log('Found post like buttons:', postButtons.length);
    
    postButtons.forEach((btn, i) => {
        console.log(`Button ${i}:`, {
            slug: btn.dataset.slug,
            username: btn.dataset.username,
            hasIcon: !!btn.querySelector('i[data-feather="heart"], .like-icon'),
            hasCount: !!btn.querySelector('.likes-count'),
            classes: btn.className
        });
    });
    
    // Test comment like buttons
    const commentButtons = document.querySelectorAll('.comment-like-button[data-comment-id]');
    console.log('Found comment like buttons:', commentButtons.length);
    
    // Test click handler
    document.body.addEventListener('click', function(e) {
        const likeBtn = e.target.closest('.like-button, .comment-like-button');
        if (likeBtn) {
            console.log('Like button clicked!', likeBtn);
        }
    });
    
    // Test CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    const csrfToken = getCookie('csrftoken');
    console.log('CSRF token found:', !!csrfToken);
    
    // Test if likes.js is loaded
    setTimeout(() => {
        console.log('Body has like-initialized:', document.body.hasAttribute('data-like-initialized'));
    }, 1000);
});