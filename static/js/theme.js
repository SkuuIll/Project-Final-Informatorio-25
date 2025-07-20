
(function() {
    const savedTheme = localStorage.getItem('devblog-theme');
    const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
})();

tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                'light-bg': '#f8fafc',
                'light-card': '#ffffff',
                'dark-bg': '#0f172a',
                'dark-card': '#1e293b',
            }
        }
    }
}
