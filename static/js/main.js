function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

document.addEventListener('DOMContentLoaded', function() {
    // Utility function to show loading state
    function setLoadingState(button, isLoading) {
        if (isLoading) {
            button.classList.add('opacity-50', 'pointer-events-none');
            button.style.transform = 'scale(0.95)';
        } else {
            button.classList.remove('opacity-50', 'pointer-events-none');
            button.style.transform = 'scale(1)';
        }
    }

    // Utility function to animate like count
    function animateLikeCount(element, newCount) {
        element.style.transform = 'scale(1.3)';
        element.textContent = newCount;
        setTimeout(() => {
            element.style.transform = 'scale(1)';
        }, 200);
    }

    // Handle post like buttons
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const username = this.dataset.username;
            const slug = this.dataset.slug;
            const url = `/post/${username}/${slug}/like/`;
            const icon = this.querySelector('.like-icon');
            const countSpan = this.querySelector('.likes-count');

            // Prevent multiple clicks
            if (this.classList.contains('processing')) return;
            
            setLoadingState(this, true);
            this.classList.add('processing');

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
                if (response.status === 302 || response.status === 401 || response.redirected) {
                    // Handle authentication redirect
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    return;
                }
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data && data.success) {
                    // Update visual state with animation
                    if (data.liked) {
                        icon.classList.add('text-red-500', 'fill-current');
                        icon.style.transform = 'scale(1.2)';
                        setTimeout(() => {
                            icon.style.transform = 'scale(1)';
                        }, 150);
                    } else {
                        icon.classList.remove('text-red-500', 'fill-current');
                    }
                    
                    // Animate count change
                    animateLikeCount(countSpan, data.likes_count);
                    
                    // Add success feedback
                    this.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        this.style.transform = 'scale(1)';
                    }, 100);
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                // Show user-friendly error
                const errorMsg = error.message.includes('Failed to fetch') 
                    ? 'Error de conexión. Por favor, intenta de nuevo.' 
                    : 'Error al procesar el like. Intenta nuevamente.';
                
                // Create temporary error message
                const errorDiv = document.createElement('div');
                errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
                errorDiv.textContent = errorMsg;
                document.body.appendChild(errorDiv);
                
                setTimeout(() => {
                    errorDiv.remove();
                }, 3000);
            })
            .finally(() => {
                setLoadingState(this, false);
                this.classList.remove('processing');
            });
        });
    });

    // Handle comment like buttons
    const commentLikeButtons = document.querySelectorAll('.comment-like-button');
    commentLikeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const commentId = this.dataset.commentId;
            const url = `/comment/${commentId}/like/`;
            const icon = this.querySelector('.like-icon');
            const countSpan = this.querySelector('.likes-count');

            // Prevent multiple clicks
            if (this.classList.contains('processing')) return;
            
            setLoadingState(this, true);
            this.classList.add('processing');

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
                if (response.status === 302 || response.status === 401 || response.redirected) {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    return;
                }
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data && data.success) {
                    // Update visual state with animation
                    if (data.liked) {
                        icon.classList.add('text-red-500', 'fill-current');
                        icon.style.transform = 'scale(1.2)';
                        setTimeout(() => {
                            icon.style.transform = 'scale(1)';
                        }, 150);
                    } else {
                        icon.classList.remove('text-red-500', 'fill-current');
                    }
                    
                    // Animate count change
                    animateLikeCount(countSpan, data.likes_count);
                    
                    // Add success feedback
                    this.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        this.style.transform = 'scale(1)';
                    }, 100);
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                const errorMsg = error.message.includes('Failed to fetch') 
                    ? 'Error de conexión. Por favor, intenta de nuevo.' 
                    : 'Error al procesar el like. Intenta nuevamente.';
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
                errorDiv.textContent = errorMsg;
                document.body.appendChild(errorDiv);
                
                setTimeout(() => {
                    errorDiv.remove();
                }, 3000);
            })
            .finally(() => {
                setLoadingState(this, false);
                this.classList.remove('processing');
            });
        });
    });

    // Add CSS for smooth transitions
    const style = document.createElement('style');
    style.textContent = `
        .like-button, .comment-like-button {
            transition: all 0.2s ease-in-out;
        }
        .like-button i, .comment-like-button i {
            transition: all 0.2s ease-in-out;
        }
        .likes-count {
            transition: all 0.2s ease-in-out;
            display: inline-block;
        }
    `;
    document.head.appendChild(style);
});
