// Share Menu System - Vanilla JavaScript implementation
(function() {
    'use strict';

    function initializeShareMenu() {
        // Find all share buttons and menus
        const shareButtons = document.querySelectorAll('[data-share-button]');
        const shareMenus = document.querySelectorAll('[data-share-menu]');

        shareButtons.forEach((button, index) => {
            const menu = shareMenus[index];
            if (!menu) return;

            let isOpen = false;

            // Toggle menu on button click
            button.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                isOpen = !isOpen;
                
                if (isOpen) {
                    menu.style.display = 'block';
                    menu.classList.remove('opacity-0', 'scale-95');
                    menu.classList.add('opacity-100', 'scale-100');
                } else {
                    menu.classList.remove('opacity-100', 'scale-100');
                    menu.classList.add('opacity-0', 'scale-95');
                    setTimeout(() => {
                        if (!isOpen) menu.style.display = 'none';
                    }, 150);
                }
            });

            // Close menu when clicking outside
            document.addEventListener('click', function(e) {
                if (!button.contains(e.target) && !menu.contains(e.target)) {
                    if (isOpen) {
                        isOpen = false;
                        menu.classList.remove('opacity-100', 'scale-100');
                        menu.classList.add('opacity-0', 'scale-95');
                        setTimeout(() => {
                            if (!isOpen) menu.style.display = 'none';
                        }, 150);
                    }
                }
            });

            // Close menu on escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && isOpen) {
                    isOpen = false;
                    menu.classList.remove('opacity-100', 'scale-100');
                    menu.classList.add('opacity-0', 'scale-95');
                    setTimeout(() => {
                        if (!isOpen) menu.style.display = 'none';
                    }, 150);
                }
            });
        });

        console.log('Share menu system initialized');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeShareMenu);
    } else {
        initializeShareMenu();
    }

    // Re-initialize on page changes
    window.addEventListener('load', initializeShareMenu);

    // Global function for copying to clipboard
    window.copyToClipboard = function(text) {
        if (navigator.clipboard && window.isSecureContext) {
            // Use modern clipboard API
            navigator.clipboard.writeText(text).then(() => {
                showToast('Enlace copiado al portapapeles', 'success');
            }).catch(() => {
                fallbackCopyToClipboard(text);
            });
        } else {
            // Fallback for older browsers
            fallbackCopyToClipboard(text);
        }
    };

    function fallbackCopyToClipboard(text) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            showToast('Enlace copiado al portapapeles', 'success');
        } catch (err) {
            showToast('No se pudo copiar el enlace', 'error');
        }
        
        document.body.removeChild(textArea);
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

})();