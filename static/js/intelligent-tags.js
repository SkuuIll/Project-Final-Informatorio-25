/**
 * Sistema de Tags Inteligente
 * Proporciona autocompletado, sugerencias y validación de tags
 */

class IntelligentTagSystem {
    constructor(options = {}) {
        this.options = {
            inputSelector: '#id_tags',
            suggestionsContainer: '#tag-suggestions',
            maxTags: 10,
            minQueryLength: 2,
            debounceDelay: 300,
            apiEndpoints: {
                suggest: '/api/tags/suggest/',
                keywords: '/api/tags/keywords/',
                related: '/api/tags/related/',
                popular: '/api/tags/popular/',
            },
            ...options
        };
        
        this.input = null;
        this.suggestionsContainer = null;
        this.selectedTags = new Set();
        this.debounceTimer = null;
        this.currentSuggestions = [];
        this.keywordExtractor = null;
        
        this.init();
    }
    
    init() {
        this.input = document.querySelector(this.options.inputSelector);
        if (!this.input) {
            console.warn('Tag input not found:', this.options.inputSelector);
            return;
        }
        
        this.createUI();
        this.bindEvents();
        this.loadInitialTags();
        this.loadPopularTags();
    }
    
    createUI() {
        // Crear contenedor principal
        const container = document.createElement('div');
        container.className = 'intelligent-tags-container relative';
        
        // Ocultar input original
        this.input.style.display = 'none';
        
        // Crear input visual
        const visualInput = document.createElement('input');
        visualInput.type = 'text';
        visualInput.className = this.input.className;
        visualInput.placeholder = 'Escribe para buscar tags o agregar nuevos...';
        visualInput.id = 'tag-visual-input';
        
        // Crear contenedor de tags seleccionados
        const selectedTagsContainer = document.createElement('div');
        selectedTagsContainer.className = 'selected-tags-container flex flex-wrap gap-2 mb-3';
        selectedTagsContainer.id = 'selected-tags';
        
        // Crear contenedor de sugerencias
        const suggestionsContainer = document.createElement('div');
        suggestionsContainer.className = 'tag-suggestions-container absolute z-50 w-full bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg shadow-lg mt-1 max-h-64 overflow-y-auto hidden';
        suggestionsContainer.id = 'tag-suggestions';
        
        // Crear sección de tags populares
        const popularTagsContainer = document.createElement('div');
        popularTagsContainer.className = 'popular-tags-container mt-3';
        popularTagsContainer.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Tags Populares</span>
                <button type="button" id="toggle-popular" class="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300">
                    Mostrar más
                </button>
            </div>
            <div id="popular-tags" class="flex flex-wrap gap-2"></div>
        `;
        
        // Crear sección de sugerencias por contenido
        const contentSuggestionsContainer = document.createElement('div');
        contentSuggestionsContainer.className = 'content-suggestions-container mt-3 hidden';
        contentSuggestionsContainer.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-slate-700 dark:text-slate-300">Sugerencias del Contenido</span>
                <button type="button" id="refresh-suggestions" class="text-xs text-green-600 dark:text-green-400 hover:text-green-800 dark:hover:text-green-300">
                    <i data-feather="refresh-cw" class="w-3 h-3 inline mr-1"></i>Actualizar
                </button>
            </div>
            <div id="content-suggestions" class="flex flex-wrap gap-2"></div>
        `;
        
        // Ensamblar UI
        container.appendChild(selectedTagsContainer);
        container.appendChild(visualInput);
        container.appendChild(suggestionsContainer);
        container.appendChild(popularTagsContainer);
        container.appendChild(contentSuggestionsContainer);
        
        // Insertar después del input original
        this.input.parentNode.insertBefore(container, this.input.nextSibling);
        
        // Guardar referencias
        this.visualInput = visualInput;
        this.selectedTagsContainer = selectedTagsContainer;
        this.suggestionsContainer = suggestionsContainer;
        this.popularTagsContainer = popularTagsContainer.querySelector('#popular-tags');
        this.contentSuggestionsContainer = contentSuggestionsContainer.querySelector('#content-suggestions');
        this.contentSuggestionsSection = contentSuggestionsContainer;
    }
    
    bindEvents() {
        // Eventos del input visual
        this.visualInput.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });
        
        this.visualInput.addEventListener('keydown', (e) => {
            this.handleKeydown(e);
        });
        
        this.visualInput.addEventListener('focus', () => {
            this.showSuggestions();
        });
        
        // Cerrar sugerencias al hacer clic fuera
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.intelligent-tags-container')) {
                this.hideSuggestions();
            }
        });
        
        // Botón de tags populares
        const togglePopular = document.getElementById('toggle-popular');
        if (togglePopular) {
            togglePopular.addEventListener('click', () => {
                this.togglePopularTags();
            });
        }
        
        // Botón de actualizar sugerencias
        const refreshSuggestions = document.getElementById('refresh-suggestions');
        if (refreshSuggestions) {
            refreshSuggestions.addEventListener('click', () => {
                this.generateContentSuggestions();
            });
        }
        
        // Detectar cambios en el contenido para sugerencias automáticas
        this.watchContentChanges();
    }
    
    handleInput(value) {
        clearTimeout(this.debounceTimer);
        
        if (value.length >= this.options.minQueryLength) {
            this.debounceTimer = setTimeout(() => {
                this.fetchSuggestions(value);
            }, this.options.debounceDelay);
        } else if (value.length === 0) {
            this.showPopularTags();
        } else {
            this.hideSuggestions();
        }
    }
    
    handleKeydown(e) {
        switch (e.key) {
            case 'Enter':
            case ',':
                e.preventDefault();
                const value = this.visualInput.value.trim();
                if (value) {
                    this.addTag(value);
                    this.visualInput.value = '';
                    this.hideSuggestions();
                }
                break;
                
            case 'Backspace':
                if (this.visualInput.value === '' && this.selectedTags.size > 0) {
                    const lastTag = Array.from(this.selectedTags).pop();
                    this.removeTag(lastTag);
                }
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                this.navigateSuggestions('down');
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.navigateSuggestions('up');
                break;
                
            case 'Escape':
                this.hideSuggestions();
                break;
        }
    }
    
    async fetchSuggestions(query) {
        try {
            const response = await fetch(`${this.options.apiEndpoints.suggest}?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displaySuggestions(data.suggestions || []);
            }
        } catch (error) {
            console.error('Error fetching tag suggestions:', error);
        }
    }
    
    async loadPopularTags() {
        try {
            const response = await fetch(this.options.apiEndpoints.popular, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayPopularTags(data.tags || []);
            }
        } catch (error) {
            console.error('Error loading popular tags:', error);
        }
    }
    
    async generateContentSuggestions() {
        const titleInput = document.querySelector('#id_title');
        const contentEditor = window.editor; // Asumiendo que el editor está disponible globalmente
        
        if (!titleInput || !contentEditor) return;
        
        const title = titleInput.value;
        const content = contentEditor.getData();
        
        if (!title && !content) return;
        
        try {
            const response = await fetch(this.options.apiEndpoints.keywords, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    title: title,
                    content: content
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.displayContentSuggestions(data.suggestions || []);
                this.contentSuggestionsSection.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error generating content suggestions:', error);
        }
    }
    
    displaySuggestions(suggestions) {
        this.currentSuggestions = suggestions;
        this.suggestionsContainer.innerHTML = '';
        
        if (suggestions.length === 0) {
            this.suggestionsContainer.innerHTML = `
                <div class="p-3 text-sm text-slate-500 dark:text-slate-400 text-center">
                    No se encontraron sugerencias
                </div>
            `;
        } else {
            suggestions.forEach((suggestion, index) => {
                const item = this.createSuggestionItem(suggestion, index);
                this.suggestionsContainer.appendChild(item);
            });
        }
        
        this.showSuggestions();
    }
    
    createSuggestionItem(suggestion, index) {
        const item = document.createElement('div');
        item.className = 'suggestion-item flex items-center justify-between p-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer border-b border-slate-100 dark:border-slate-600 last:border-b-0';
        item.dataset.index = index;
        
        const leftContent = document.createElement('div');
        leftContent.className = 'flex items-center space-x-3';
        
        const tagName = document.createElement('span');
        tagName.className = 'font-medium text-slate-900 dark:text-slate-100';
        tagName.textContent = suggestion.name || suggestion.tag || suggestion;
        
        const tagInfo = document.createElement('div');
        tagInfo.className = 'text-xs text-slate-500 dark:text-slate-400';
        
        if (suggestion.usage_count) {
            tagInfo.textContent = `${suggestion.usage_count} posts`;
        }
        
        if (suggestion.is_trending) {
            const trendingBadge = document.createElement('span');
            trendingBadge.className = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200 ml-2';
            trendingBadge.innerHTML = '<i data-feather="trending-up" class="w-3 h-3 mr-1"></i>Trending';
            tagInfo.appendChild(trendingBadge);
        }
        
        leftContent.appendChild(tagName);
        if (tagInfo.textContent || tagInfo.children.length > 0) {
            leftContent.appendChild(tagInfo);
        }
        
        item.appendChild(leftContent);
        
        // Evento de clic
        item.addEventListener('click', () => {
            this.addTag(suggestion.name || suggestion.tag || suggestion);
            this.visualInput.value = '';
            this.hideSuggestions();
        });
        
        return item;
    }
    
    displayPopularTags(tags) {
        this.popularTagsContainer.innerHTML = '';
        
        tags.slice(0, 8).forEach(tag => {
            const tagElement = this.createPopularTagElement(tag);
            this.popularTagsContainer.appendChild(tagElement);
        });
    }
    
    displayContentSuggestions(suggestions) {
        this.contentSuggestionsContainer.innerHTML = '';
        
        suggestions.slice(0, 10).forEach(suggestion => {
            const tagElement = this.createContentSuggestionElement(suggestion);
            this.contentSuggestionsContainer.appendChild(tagElement);
        });
    }
    
    createPopularTagElement(tag) {
        const element = document.createElement('button');
        element.type = 'button';
        element.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors';
        element.textContent = tag.name || tag;
        
        element.addEventListener('click', () => {
            this.addTag(tag.name || tag);
        });
        
        return element;
    }
    
    createContentSuggestionElement(suggestion) {
        const element = document.createElement('button');
        element.type = 'button';
        element.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-800 transition-colors';
        
        const text = document.createElement('span');
        text.textContent = suggestion.keyword || suggestion;
        
        if (suggestion.score) {
            const score = document.createElement('span');
            score.className = 'ml-2 text-xs opacity-75';
            score.textContent = `${Math.round(suggestion.score * 100)}%`;
            element.appendChild(text);
            element.appendChild(score);
        } else {
            element.appendChild(text);
        }
        
        element.addEventListener('click', () => {
            this.addTag(suggestion.keyword || suggestion);
        });
        
        return element;
    }
    
    addTag(tagText) {
        if (this.selectedTags.size >= this.options.maxTags) {
            this.showMessage(`Máximo ${this.options.maxTags} tags permitidos`, 'warning');
            return;
        }
        
        // Normalizar tag
        const normalizedTag = tagText.toLowerCase().trim();
        
        if (this.selectedTags.has(normalizedTag)) {
            this.showMessage('Este tag ya está agregado', 'info');
            return;
        }
        
        if (normalizedTag.length < 2) {
            this.showMessage('Los tags deben tener al menos 2 caracteres', 'error');
            return;
        }
        
        this.selectedTags.add(normalizedTag);
        this.updateSelectedTagsDisplay();
        this.updateHiddenInput();
        this.showMessage(`Tag "${normalizedTag}" agregado`, 'success');
    }
    
    removeTag(tagText) {
        this.selectedTags.delete(tagText);
        this.updateSelectedTagsDisplay();
        this.updateHiddenInput();
    }
    
    updateSelectedTagsDisplay() {
        this.selectedTagsContainer.innerHTML = '';
        
        this.selectedTags.forEach(tag => {
            const tagElement = document.createElement('div');
            tagElement.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200';
            
            const tagText = document.createElement('span');
            tagText.textContent = tag;
            
            const removeButton = document.createElement('button');
            removeButton.type = 'button';
            removeButton.className = 'ml-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-200';
            removeButton.innerHTML = '<i data-feather="x" class="w-3 h-3"></i>';
            
            removeButton.addEventListener('click', () => {
                this.removeTag(tag);
            });
            
            tagElement.appendChild(tagText);
            tagElement.appendChild(removeButton);
            this.selectedTagsContainer.appendChild(tagElement);
        });
        
        // Actualizar iconos de Feather
        if (window.feather) {
            feather.replace();
        }
    }
    
    updateHiddenInput() {
        this.input.value = Array.from(this.selectedTags).join(', ');
    }
    
    loadInitialTags() {
        if (this.input.value) {
            const tags = this.input.value.split(',').map(tag => tag.trim()).filter(tag => tag);
            tags.forEach(tag => this.selectedTags.add(tag.toLowerCase()));
            this.updateSelectedTagsDisplay();
        }
    }
    
    showSuggestions() {
        this.suggestionsContainer.classList.remove('hidden');
    }
    
    hideSuggestions() {
        this.suggestionsContainer.classList.add('hidden');
    }
    
    showPopularTags() {
        // Mostrar tags populares cuando no hay query
        this.suggestionsContainer.innerHTML = `
            <div class="p-3">
                <div class="text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Tags Populares</div>
                <div id="popular-suggestions" class="flex flex-wrap gap-2"></div>
            </div>
        `;
        
        const container = this.suggestionsContainer.querySelector('#popular-suggestions');
        // Reutilizar los tags populares ya cargados
        Array.from(this.popularTagsContainer.children).slice(0, 6).forEach(tag => {
            const clone = tag.cloneNode(true);
            clone.addEventListener('click', () => {
                this.addTag(clone.textContent);
                this.visualInput.value = '';
                this.hideSuggestions();
            });
            container.appendChild(clone);
        });
        
        this.showSuggestions();
    }
    
    togglePopularTags() {
        const button = document.getElementById('toggle-popular');
        const isExpanded = this.popularTagsContainer.children.length > 8;
        
        if (isExpanded) {
            // Mostrar solo los primeros 8
            Array.from(this.popularTagsContainer.children).slice(8).forEach(child => {
                child.style.display = 'none';
            });
            button.textContent = 'Mostrar más';
        } else {
            // Mostrar todos
            Array.from(this.popularTagsContainer.children).forEach(child => {
                child.style.display = 'inline-flex';
            });
            button.textContent = 'Mostrar menos';
        }
    }
    
    watchContentChanges() {
        // Observar cambios en el título
        const titleInput = document.querySelector('#id_title');
        if (titleInput) {
            titleInput.addEventListener('input', () => {
                clearTimeout(this.contentChangeTimer);
                this.contentChangeTimer = setTimeout(() => {
                    this.generateContentSuggestions();
                }, 2000);
            });
        }
        
        // Observar cambios en el editor (si está disponible)
        if (window.editor) {
            window.editor.model.document.on('change:data', () => {
                clearTimeout(this.contentChangeTimer);
                this.contentChangeTimer = setTimeout(() => {
                    this.generateContentSuggestions();
                }, 3000);
            });
        }
    }
    
    navigateSuggestions(direction) {
        const items = this.suggestionsContainer.querySelectorAll('.suggestion-item');
        if (items.length === 0) return;
        
        const currentActive = this.suggestionsContainer.querySelector('.suggestion-item.active');
        let newIndex = 0;
        
        if (currentActive) {
            const currentIndex = parseInt(currentActive.dataset.index);
            newIndex = direction === 'down' 
                ? Math.min(currentIndex + 1, items.length - 1)
                : Math.max(currentIndex - 1, 0);
            currentActive.classList.remove('active');
        }
        
        items[newIndex].classList.add('active');
        items[newIndex].scrollIntoView({ block: 'nearest' });
    }
    
    showMessage(message, type = 'info') {
        // Crear o actualizar mensaje
        let messageEl = document.getElementById('tag-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'tag-message';
            messageEl.className = 'fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 transform translate-x-full';
            document.body.appendChild(messageEl);
        }
        
        // Configurar estilos según el tipo
        const styles = {
            success: 'bg-green-100 text-green-800 border border-green-200',
            error: 'bg-red-100 text-red-800 border border-red-200',
            warning: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
            info: 'bg-blue-100 text-blue-800 border border-blue-200'
        };
        
        messageEl.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${styles[type]}`;
        messageEl.textContent = message;
        
        // Mostrar mensaje
        setTimeout(() => {
            messageEl.style.transform = 'translateX(0)';
        }, 10);
        
        // Ocultar después de 3 segundos
        setTimeout(() => {
            messageEl.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.parentNode.removeChild(messageEl);
                }
            }, 300);
        }, 3000);
    }
    
    getCSRFToken() {
        const token = document.querySelector('input[name="csrfmiddlewaretoken"]');
        return token ? token.value : '';
    }
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('#id_tags')) {
        window.intelligentTags = new IntelligentTagSystem();
    }
});

// Exportar para uso global
window.IntelligentTagSystem = IntelligentTagSystem;