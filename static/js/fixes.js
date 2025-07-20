document.addEventListener('DOMContentLoaded', () => {
    // Inicializar Feather Icons
    feather.replace();
    
    // ===== SISTEMA DE TEMAS MEJORADO =====
    const themeToggleBtn = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    
    function getTheme() {
        const stored = localStorage.getItem('devblog-theme');
        if (stored) return stored;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    function setTheme(theme) {
        const isDark = theme === 'dark';
        document.documentElement.classList.toggle('dark', isDark);
        document.documentElement.style.colorScheme = theme;
        localStorage.setItem('devblog-theme', theme);
        updateThemeIcon();
        
        // Mostrar toast de confirmación
        showToast(isDark ? 'Tema oscuro activado' : 'Tema claro activado', 'success');
    }

    function updateThemeIcon() {
        const isDark = document.documentElement.classList.contains('dark');
        darkIcon.classList.toggle('hidden', isDark);
        lightIcon.classList.toggle('hidden', !isDark);
    }
    
    updateThemeIcon();
    
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = getTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    // ===== INDICADOR DE SCROLL =====
    const scrollIndicator = document.getElementById('scroll-indicator');
    
    function updateScrollIndicator() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        const scrollPercentage = (scrollTop / scrollHeight) * 100;
        scrollIndicator.style.transform = `scaleX(${scrollPercentage / 100})`;
    }
    
    // ===== BOTÓN VOLVER ARRIBA =====
    const backToTopBtn = document.getElementById('back-to-top');
    
    function toggleBackToTop() {
        if (window.pageYOffset > 300) {
            backToTopBtn.classList.remove('opacity-0', 'invisible');
            backToTopBtn.classList.add('opacity-100', 'visible');
        } else {
            backToTopBtn.classList.add('opacity-0', 'invisible');
            backToTopBtn.classList.remove('opacity-100', 'visible');
        }
    }
    
    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // ===== MENÚ MÓVIL =====
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');

    mobileMenuToggle.addEventListener('click', () => {
        const isExpanded = mobileMenuToggle.getAttribute('aria-expanded') === 'true';
        mobileMenu.classList.toggle('hidden');
        mobileMenuToggle.setAttribute('aria-expanded', !isExpanded);
        
        // Animar el icono
        const icon = mobileMenuToggle.querySelector('i');
        if (isExpanded) {
            icon.setAttribute('data-feather', 'menu');
        } else {
            icon.setAttribute('data-feather', 'x');
        }
        feather.replace();
    });

    // ===== MENÚ DE USUARIO =====
    const userMenuDropdown = document.getElementById('user-menu-dropdown');
    if (userMenuDropdown) {
        const userMenuButton = document.getElementById('user-menu-button');
        const userMenu = document.getElementById('user-menu');

        if (userMenuButton && userMenu) {
            console.log('User menu elements found:', { userMenuButton, userMenu });
            
            const toggleUserMenu = () => {
                const isExpanded = userMenuButton.getAttribute('aria-expanded') === 'true';
                console.log('Toggling user menu. Current expanded state:', isExpanded);
                
                if (isExpanded) {
                    userMenu.classList.add('hidden');
                    userMenuButton.setAttribute('aria-expanded', 'false');
                } else {
                    userMenu.classList.remove('hidden');
                    userMenuButton.setAttribute('aria-expanded', 'true');
                }
                
                console.log('Menu toggled. New state:', userMenuButton.getAttribute('aria-expanded'));
            };

            userMenuButton.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                console.log('User menu button clicked');
                toggleUserMenu();
            });

            // Cerrar menú al hacer clic fuera
            document.addEventListener('click', (event) => {
                if (!userMenuDropdown.contains(event.target)) {
                    userMenu.classList.add('hidden');
                    userMenuButton.setAttribute('aria-expanded', 'false');
                }
            });
            
            // Cerrar menú con ESC
            document.addEventListener('keydown', (event) => {
                if (event.key === 'Escape' && userMenuButton.getAttribute('aria-expanded') === 'true') {
                    toggleUserMenu();
                    userMenuButton.focus();
                }
            });
        } else {
            console.error('User menu elements not found:', { userMenuButton, userMenu });
        }
    } else {
        console.error('User menu dropdown container not found');
    }

    // ===== SISTEMA DE NOTIFICACIONES TOAST =====
    function showToast(message, type = 'info', duration = 3000) {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        const bgColor = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        }[type];
        
        toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg transform transition-all duration-300 translate-x-full opacity-0`;
        toast.textContent = message;
        
        toastContainer.appendChild(toast);
        
        // Animar entrada
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        }, 100);
        
        // Animar salida
        setTimeout(() => {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => {
                if (toast.parentNode === toastContainer) {
                   toastContainer.removeChild(toast);
                }
            }, 300);
        }, duration);
    }
    
    // Exponer función globalmente
    window.showToast = showToast;

    // ===== ANIMACIONES AL HACER SCROLL =====
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });

    // ===== BÚSQUEDA MEJORADA =====
    const searchInputs = document.querySelectorAll('input[type="search"]');
    
    searchInputs.forEach(input => {
        let searchTimeout;
        
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length > 2) {
                searchTimeout = setTimeout(() => {
                    // SUGERENCIA: Aquí puedes implementar una llamada fetch a una API de Django
                    // para obtener sugerencias de búsqueda en tiempo real.
                    // Ejemplo: fetch(`/posts/search/?q=${query}`, { headers: { 'X-CSRFToken': csrftoken } })
                    console.log('Buscando sugerencias para:', query);
                }, 300);
            }
        });
        
        // Limpiar búsqueda con ESC
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                this.blur();
            }
        });
    });

    // ===== SCROLL SUAVE PARA ENLACES DE ANCLA =====
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = 80; // Altura del header sticky
                const targetPosition = targetElement.offsetTop - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });

    // ===== MEJORAR RENDIMIENTO =====
    // Lazy loading para imágenes
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    }

    // ===== OPTIMIZAR EVENTOS DE SCROLL =====
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        }
    }
    
    const optimizedScroll = throttle(() => {
        updateScrollIndicator();
        toggleBackToTop();
    }, 16); // ~60fps

    window.addEventListener('scroll', optimizedScroll);

    // ===== FUNCIÓN PARA OBTENER CSRF TOKEN =====
    function getCSRFToken() {
        // Primero intentar obtener desde window.csrfToken
        if (window.csrfToken) {
            return window.csrfToken;
        }
        
        // Fallback: obtener desde cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return value;
            }
        }
        
        // Fallback: obtener desde meta tag
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        if (csrfMeta) {
            return csrfMeta.getAttribute('content');
        }
        
        return null;
    }

    // ===== LIKE AND FAVORITE BUTTONS =====
    document.querySelectorAll('.like-button').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            console.log("Like button clicked:", this);
            const icon = this.querySelector('svg');
            console.log("Icon found:", icon);

            if (!icon) {
                console.error("SVG icon not found inside the button.");
                return;
            }

            const username = this.dataset.username;
            const slug = this.dataset.slug;
            const url = `/post/${username}/${slug}/like/`;
            const likesCountSpan = this.querySelector('.likes-count');
            
            // Verificar si el usuario está autenticado
            const csrfToken = getCSRFToken();
            if (!csrfToken) {
                showToast('Debes iniciar sesión para dar me gusta', 'warning');
                // Redirigir a la página de login después de un breve delay
                setTimeout(() => {
                    window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                }, 1500);
                return;
            }
            
            // Deshabilitar botón temporalmente para evitar clicks múltiples
            this.disabled = true;
            this.style.opacity = '0.6';

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401) {
                        throw new Error('Debes iniciar sesión para dar me gusta');
                    } else if (response.status === 403) {
                        throw new Error('No tienes permisos para realizar esta acción');
                    } else {
                        throw new Error(`Error del servidor: ${response.status}`);
                    }
                }
                return response.json();
            })
            .then(data => {
                // Verificar si hay un error en la respuesta JSON
                if (data.error) {
                    throw new Error(data.error);
                }
                return data;
            })
            .then(data => {
                // Actualizar contador
                if (data.likes_count !== undefined && likesCountSpan) {
                    likesCountSpan.textContent = data.likes_count;
                }
                
                // Actualizar estado visual del botón
                if (data.liked) {
                    icon.classList.add('text-red-500', 'fill-current');
                    showToast('¡Te gusta este post!', 'success', 2000);
                } else {
                    icon.classList.remove('text-red-500', 'fill-current');
                    showToast('Ya no te gusta este post', 'info', 2000);
                }
                
                // Animación del botón
                icon.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    icon.style.transform = 'scale(1)';
                }, 200);
            })
            .catch(error => {
                console.error('Error al dar me gusta:', error);
                
                // Manejar diferentes tipos de errores
                if (error.message.includes('iniciar sesión')) {
                    showToast('Debes iniciar sesión para dar me gusta', 'warning');
                    setTimeout(() => {
                        window.location.href = '/accounts/login/?next=' + encodeURIComponent(window.location.pathname);
                    }, 1500);
                } else {
                    showToast(error.message || 'Error al procesar la solicitud', 'error');
                }
            })
            .finally(() => {
                // Rehabilitar botón
                this.disabled = false;
                this.style.opacity = '1';
            });
        });
    });

    const favoriteButton = document.getElementById('favorite-button');

    if (favoriteButton) {
        favoriteButton.addEventListener('click', function(e) {
            e.preventDefault();
            fetch(this.dataset.url)
                .then(response => response.json())
                .then(data => {
                    const icon = this.querySelector('i');
                    if (data.favorited) {
                        icon.classList.add('text-amber-500', 'fill-current');
                    } else {
                        icon.classList.remove('text-amber-500', 'fill-current');
                    }
                });
        });
    }

    // ===== INICIALIZACIÓN FINAL =====
    console.log('DevBlog initialized successfully! 🚀');
    
    // Mostrar mensaje de bienvenida si es la primera visita
    if (!localStorage.getItem('devblog-visited')) {
        setTimeout(() => {
            showToast('¡Bienvenido a DevBlog! 👋', 'success', 5000);
            localStorage.setItem('devblog-visited', 'true');
        }, 1000);
    }
});

// ===== FUNCIONES GLOBALES (para usarlas desde otras plantillas si es necesario) =====
window.DevBlog = {
    showToast: (message, type, duration) => {
        // Asegura que la función esté disponible incluso si el DOM no está listo
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => showToast(message, type, duration));
        } else {
            showToast(message, type, duration);
        }
    },
    copyToClipboard: (text) => {
        navigator.clipboard.writeText(text).then(() => {
            window.DevBlog.showToast('Texto copiado al portapapeles', 'success');
        }).catch(() => {
            window.DevBlog.showToast('Error al copiar texto', 'error');
        });
    }
};
