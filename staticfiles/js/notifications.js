document.addEventListener('DOMContentLoaded', () => {
    const notificationSocket = new WebSocket(
        'ws://'
        + window.location.host
        + '/ws/notifications/'
    );

    notificationSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (typeof window.showToast === 'function') {
            window.showToast(data.message, 'info');
        }
        const notificationBadge = document.querySelector('.notification-badge');
        if (notificationBadge) {
            const currentCount = parseInt(notificationBadge.textContent) || 0;
            notificationBadge.textContent = currentCount + 1;
            notificationBadge.classList.remove('hidden');
        }
        try {
            const unreadCountSpan = document.querySelector('#user-menu a[href="{% url "accounts:notification_list" %}"] span.ml-auto');
            if(unreadCountSpan){
                const currentUnreadCount = parseInt(unreadCountSpan.textContent) || 0;
                unreadCountSpan.textContent = currentUnreadCount + 1;
                unreadCountSpan.classList.remove('hidden');
            }
        } catch(e) {
            console.log('Error updating notification count:', e);
        }
    };

    notificationSocket.onclose = function(e) {
        console.error('Notification socket closed unexpectedly');
    };
});