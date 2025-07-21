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

document.addEventListener('DOMContentLoaded', function () {
    // Utility function to show loading state
    function setLoadingState(button, isLoading) {
        if (isLoading) {
            button.classList.add('opacity-50', 'pointer-events-none');
            button.disabled = true;
        } else {
            button.classList.remove('opacity-50', 'pointer-events-none');
            button.disabled = false;
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

    // Utility function to show error messages
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        errorDiv.textContent = message;
        document.body.appendChild(errorDiv);
        setTimeout(() => {
            errorDiv.remove();
        }, 3000);
    }

    // Utility function to show success messages
    function showSuccess(message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg z-50';
        successDiv.textContent = message;
        document.body.appendChild(successDiv);
        setTimeout(() => {
            successDiv.remove();
        }, 2000);
    }

    // Like functionality is now handled by likes.js

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
        .liked {
            background-color: rgba(239, 68, 68, 0.1);
        }
    `;
    document.head.appendChild(style);
});
