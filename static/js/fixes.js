// Correcciones de JavaScript para DevBlog

document.addEventListener('DOMContentLoaded', function() {
    
    // Inicializar Feather Icons de forma segura
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Función para mostrar toast notifications de forma segura
    window.showToast = function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        
        const toast = document.createElement('div');
        toast.className = `toast-notification bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg p-4 shadow-lg transform transition-all duration-300 translate-x-full opacity-0`;
        
        const typeColors = {
            'info': 'border-l-4 border-l-blue-500',
            'success': 'border-l-4 border-l-green-500',
            'warning': 'border-l-4 border-l-yellow-500',
            'error': 'border-l-4 border-l-red-500'
        };
        
        toast.className += ' ' + (typeColors[type] || typeColors['info']);
        toast.innerHTML = `
            <div class="flex items-center">
                <span class="text-slate-800 dark:text-slate-200">${message}</span>
                <button class="ml-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Animar entrada
        setTimeout(() => {
            toast.classList.remove('translate-x-full', 'opacity-0');
        }, 100);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            toast.classList.add('translate-x-full', 'opacity-0');
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, 300);
        }, 5000);
    };
    
    // Manejo del scroll indicator
    const scrollIndicator = document.getElementById('scroll-indicator');
    if (scrollIndicator) {
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = (scrollTop / scrollHeight) * 100;
            scrollIndicator.style.width = scrollPercent + '%';
        });
    }
    
    // Manejo del botón back-to-top
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.pageYOffset > 300) {
                backToTopBtn.classList.remove('opacity-0', 'invisible');
                backToTopBtn.classList.add('opacity-100', 'visible');
            } else {
                backToTopBtn.classList.add('opacity-0', 'invisible');
                backToTopBtn.classList.remove('opacity-100', 'visible');
            }
        });
        
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Manejo del toggle de tema
    const themeToggle = document.getElementById('theme-toggle');
    const darkIcon = document.getElementById('theme-toggle-dark-icon');
    const lightIcon = document.getElementById('theme-toggle-light-icon');
    
    if (themeToggle && darkIcon && lightIcon) {
        // Verificar tema actual
        const isDark = document.documentElement.classList.contains('dark');
        updateThemeIcons(isDark);
        
        themeToggle.addEventListener('click', function() {
            document.documentElement.classList.toggle('dark');
            const newIsDark = document.documentElement.classList.contains('dark');
            updateThemeIcons(newIsDark);
            localStorage.setItem('theme', newIsDark ? 'dark' : 'light');
        });
        
        function updateThemeIcons(isDark) {
            if (isDark) {
                darkIcon.classList.add('hidden');
                lightIcon.classList.remove('hidden');
            } else {
                darkIcon.classList.remove('hidden');
                lightIcon.classList.add('hidden');
            }
        }
    }
    
    // Manejo del menú móvil
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuToggle && mobileMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            const isHidden = mobileMenu.classList.contains('hidden');
            if (isHidden) {
                mobileMenu.classList.remove('hidden');
                mobileMenuToggle.setAttribute('aria-expanded', 'true');
            } else {
                mobileMenu.classList.add('hidden');
                mobileMenuToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }
    
    // Manejo del menú de usuario - REMOVIDO para evitar conflictos con main.js
    // El manejo del menú de usuario se realiza en main.js
    
    // Manejo de botones de like
    const likeButtons = document.querySelectorAll('.like-button');
    likeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const slug = this.dataset.slug;
            if (!slug) return;
            
            // Aquí iría la lógica AJAX para el like
            // Por ahora solo mostramos feedback visual
            const icon = this.querySelector('i[data-feather="heart"]');
            const count = this.querySelector('.likes-count');
            
            if (icon && count) {
                if (icon.classList.contains('text-red-500')) {
                    icon.classList.remove('text-red-500', 'fill-current');
                    count.textContent = parseInt(count.textContent) - 1;
                } else {
                    icon.classList.add('text-red-500', 'fill-current');
                    count.textContent = parseInt(count.textContent) + 1;
                }
            }
        });
    });
    
    // Manejo de sugerencias de búsqueda
    const searchInputs = document.querySelectorAll('input[type="search"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Aquí iría la lógica para mostrar sugerencias
                console.log('Searching for:', this.value);
            }, 300);
        });
    });
    
    // Escuchar cambios en la preferencia del sistema (solo si no hay tema guardado)
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
            if (!localStorage.getItem('theme')) {
                if (e.matches) {
                    document.documentElement.classList.add('dark');
                } else {
                    document.documentElement.classList.remove('dark');
                }
                // Actualizar iconos del toggle
                const themeToggle = document.getElementById('theme-toggle');
                const darkIcon = document.getElementById('theme-toggle-dark-icon');
                const lightIcon = document.getElementById('theme-toggle-light-icon');
                if (themeToggle && darkIcon && lightIcon) {
                    updateThemeIcons(e.matches);
                }
            }
        });
    }
    
    // Manejo de errores globales
    window.addEventListener('error', function(e) {
        console.error('Error capturado:', e.error);
    });
    
    // Manejo de promesas rechazadas
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Promesa rechazada:', e.reason);
    });
    
});

// Función utilitaria para debounce
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// Función utilitaria para throttle
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
    };
}
