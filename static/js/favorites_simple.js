// Simple Favorites System - More robust approach
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
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-white font-medium transition-all duration-300 transform translate-x-full opacity-0 ${
            type === 'error' ? 'bg-red-500' : 
            type === 'success' ? 'bg-green-500' : 
            type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
        }`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        }, 100);

        setTimeout(() => {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    const csrftoken = getCookie('csrftoken');

    function handleFavoriteClick(event) {
        const button = event.target.closest('#favorite-button');
        if (!button) return;

        event.preventDefault();
        event.stopPropagation();

        if (button.hasAttribute('data-processing')) return;

        const url = button.getAttribute('data-url');
        if (!url) {
            showToast('Error: URL del favorito no encontrada', 'error');
            return;
        }

        // Set processing state
        button.setAttribute('data-processing', 'true');
        button.style.pointerEvents = 'none';
        button.style.opacity = '0.6';

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
                return response.json().then(data => {
                    showToast(data.error || 'Debes iniciar sesión para agregar favoritos', 'warning');
                    setTimeout(() => {
                        const redirectUrl = data.redirect || '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                        window.location.href = redirectUrl;
                    }, 1500);
                    return Promise.reject('User not authenticated');
                });
            }
            if (!response.ok) {
                return response.json().then(err => Promise.reject(err.error || 'Server error'));
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Find the icon (could be <i> or <svg>)
                const icon = button.querySelector('i, svg');
                
                if (icon) {
                    // Update icon state
                    if (data.favorited) {
                        icon.classList.add('text-amber-500');
                        if (icon.tagName === 'svg') {
                            icon.style.fill = 'currentColor';
                        } else {
                            icon.classList.add('fill-current');
                        }
                        button.setAttribute('aria-label', 'Remover de favoritos');
                    } else {
                        icon.classList.remove('text-amber-500');
                        if (icon.tagName === 'svg') {
                            icon.style.fill = 'none';
                        } else {
                            icon.classList.remove('fill-current');
                        }
                        button.setAttribute('aria-label', 'Añadir a favoritos');
                    }
                }

                // Success animation
                button.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                }, 200);

                // Show success message
                const message = data.message || (data.favorited ? 
                    'Post agregado a favoritos' : 
                    'Post removido de favoritos');
                showToast(message, 'success');

                // Re-initialize Feather icons if available
                if (typeof feather !== 'undefined') {
                    feather.replace();
                }

            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('Favorite action failed:', error);
            showToast(error.toString() || 'Error al procesar el favorito', 'error');
        })
        .finally(() => {
            // Reset button state
            button.removeAttribute('data-processing');
            button.style.pointerEvents = 'auto';
            button.style.opacity = '1';
            button.style.transform = 'scale(1)';
        });
    }

    // Initialize the system
    function init() {
        // Remove any existing listeners to prevent duplicates
        if (document.body.hasAttribute('data-favorites-initialized')) {
            return;
        }
        
        document.addEventListener('click', handleFavoriteClick);
        document.body.setAttribute('data-favorites-initialized', 'true');
        console.log('Simple favorites system initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Re-initialize on page changes
    window.addEventListener('load', function() {
        setTimeout(() => {
            init();
        }, 100);
    });

})();