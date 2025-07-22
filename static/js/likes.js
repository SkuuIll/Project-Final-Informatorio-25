// Consolidated Like System - Handles both post and comment likes
(function() {
    'use strict';

    // Utility functions
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

    function showToast(message, type = 'info') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-white font-medium transition-all duration-300 transform translate-x-full opacity-0 ${
            type === 'error' ? 'bg-red-500' : 
            type === 'success' ? 'bg-green-500' : 
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        }, 100);

        // Remove after 3 seconds
        setTimeout(() => {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    const csrftoken = getCookie('csrftoken');

    // Initialize when DOM is ready
    function initializeLikeSystem() {
        // Remove any existing listeners to prevent duplicates
        if (document.body.hasAttribute('data-like-initialized')) {
            return;
        }

        // Handle post likes
        document.body.addEventListener('click', handleLikeClick);
        document.body.setAttribute('data-like-initialized', 'true');
    }

    function handleLikeClick(e) {
        // Handle post likes
        const postLikeButton = e.target.closest('.like-button[data-slug][data-username]');
        if (postLikeButton) {
            e.preventDefault();
            e.stopPropagation();
            handlePostLike(postLikeButton);
            return;
        }

        // Handle comment likes
        const commentLikeButton = e.target.closest('.comment-like-button[data-comment-id]');
        if (commentLikeButton) {
            e.preventDefault();
            e.stopPropagation();
            handleCommentLike(commentLikeButton);
            return;
        }
    }

    function handlePostLike(button) {
        if (button.hasAttribute('data-processing')) return;

        const username = button.getAttribute('data-username');
        const slug = button.getAttribute('data-slug');

        if (!username || !slug) {
            console.error('Like button is missing data-username or data-slug attributes.');
            showToast('Error: Datos del post no encontrados', 'error');
            return;
        }

        const url = `/post/${username}/${slug}/like/`;
        const icon = button.querySelector('i[data-feather="heart"], .like-icon');
        const countSpan = button.querySelector('.likes-count');

        if (!icon || !countSpan) {
            console.error('Could not find icon or count span inside the like button.');
            showToast('Error: Elementos del botón no encontrados', 'error');
            return;
        }

        performLikeAction(button, url, icon, countSpan, 'post');
    }

    function handleCommentLike(button) {
        if (button.hasAttribute('data-processing')) return;

        const commentId = button.getAttribute('data-comment-id');
        if (!commentId) {
            console.error('Comment like button is missing data-comment-id attribute.');
            showToast('Error: ID del comentario no encontrado', 'error');
            return;
        }

        const url = `/comment/${commentId}/like/`;
        const icon = button.querySelector('i[data-feather="heart"], .like-icon');
        const countSpan = button.querySelector('.likes-count');

        if (!icon || !countSpan) {
            console.error('Could not find icon or count span inside the comment like button.');
            showToast('Error: Elementos del botón no encontrados', 'error');
            return;
        }

        performLikeAction(button, url, icon, countSpan, 'comment');
    }

    function performLikeAction(button, url, icon, countSpan, type) {
        // Set processing state
        button.setAttribute('data-processing', 'true');
        button.style.pointerEvents = 'none';
        button.style.opacity = '0.6';

        // Add loading animation
        button.style.transform = 'scale(0.95)';

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
            },
            credentials: 'same-origin'
        })
        .then(response => {
            if (response.status === 401 || response.status === 403) {
                showToast('Debes iniciar sesión para dar like', 'warning');
                setTimeout(() => {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                }, 1500);
                return Promise.reject('User not authenticated');
            }
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err.error || 'Server error'));
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Update icon state
                if (data.liked) {
                    icon.classList.add('text-red-500', 'fill-current');
                    button.classList.add('liked');
                    button.setAttribute('aria-pressed', 'true');
                } else {
                    icon.classList.remove('text-red-500', 'fill-current');
                    button.classList.remove('liked');
                    button.setAttribute('aria-pressed', 'false');
                }

                // Update likes count with animation
                const currentCount = parseInt(countSpan.textContent) || 0;
                const newCount = data.likes_count;
                
                if (currentCount !== newCount) {
                    countSpan.style.transform = 'scale(1.2)';
                    countSpan.textContent = newCount;
                    setTimeout(() => {
                        countSpan.style.transform = 'scale(1)';
                    }, 200);
                }

                // Success animation
                button.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 200);

                // Show success message
                const message = data.message || (data.liked ? 
                    `${type === 'post' ? 'Post' : 'Comentario'} marcado como favorito` : 
                    `Like removido del ${type === 'post' ? 'post' : 'comentario'}`);
                showToast(message, 'success');

                // Re-initialize Feather icons
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }

            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('Like action failed:', error);
            showToast(error.toString() || 'Error al procesar el like', 'error');
        })
        .finally(() => {
            // Reset button state
            button.removeAttribute('data-processing');
            button.style.pointerEvents = 'auto';
            button.style.opacity = '1';
            button.style.transform = 'scale(1)';
        });
    }

    // Initialize when DOM is loaded
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeLikeSystem);
    } else {
        initializeLikeSystem();
    }

    // Re-initialize on page changes (for SPA-like behavior)
    window.addEventListener('load', function() {
        // Small delay to ensure all elements are loaded
        setTimeout(() => {
            initializeLikeSystem();
            // Re-initialize Feather icons after DOM changes
            if (typeof feather !== 'undefined') {
                feather.replace();
            }
        }, 100);
    });

    // Debug: Log initialization
    console.log('Likes system script loaded');

})();

