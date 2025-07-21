/**
 * Mejoras para la funcionalidad de likes
 * Este archivo contiene correcciones y mejoras para el sistema de likes
 */

(function() {
    'use strict';

    // Obtener el token CSRF
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

    const csrftoken = getCookie('csrftoken');

    // Función para manejar likes de posts
    function handlePostLike(button) {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            const username = this.dataset.username;
            const slug = this.dataset.slug;
            const url = this.dataset.url || `/post/${username}/${slug}/like/`;
            const icon = this.querySelector('.like-icon');
            const countSpan = this.querySelector('.likes-count');

            if (this.classList.contains('processing')) return;
            
            this.classList.add('processing');
            this.disabled = true;

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
                    alert('Debes iniciar sesión para dar like');
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    return;
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Actualizar estado visual
                    if (data.liked) {
                        icon.classList.add('text-red-500', 'fill-current');
                        this.classList.add('liked');
                    } else {
                        icon.classList.remove('text-red-500', 'fill-current');
                        this.classList.remove('liked');
                    }
                    
                    // Actualizar contador
                    if (countSpan) {
                        countSpan.textContent = data.likes_count;
                    }
                    
                    // Mostrar mensaje de éxito
                    console.log(data.message || 'Like actualizado');
                } else {
                    throw new Error(data.error || 'Error desconocido');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error: ' + error.message);
            })
            .finally(() => {
                this.classList.remove('processing');
                this.disabled = false;
            });
        });
    }

    // Inicializar cuando el DOM esté listo
    document.addEventListener('DOMContentLoaded', function() {
        const likeButtons = document.querySelectorAll('.like-button');
        likeButtons.forEach(handlePostLike);
    });

})();
