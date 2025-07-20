import ClassicEditor from './src/ckeditor';
import './src/override-django.css';

/**
 * Enhanced CKEditor 5 integration for Django
 * Improved version with better error handling, performance, and maintainability
 */
class CKEditorManager {
    constructor() {
        this.editors = new Map();
        this.callbacks = new Map();
        this.observer = null;
        this.isInitialized = false;
        
        // Bind methods to preserve context
        this.handleFormsetAdded = this.handleFormsetAdded.bind(this);
        this.handleMutations = this.handleMutations.bind(this);
        
        // Expose global interface
        this.exposeGlobalInterface();
    }

    /**
     * Expose global interface for backwards compatibility
     */
    exposeGlobalInterface() {
        window.ClassicEditor = ClassicEditor;
        window.ckeditorRegisterCallback = this.registerCallback.bind(this);
        window.ckeditorUnregisterCallback = this.unregisterCallback.bind(this);
        window.editors = this.editors;
    }

    /**
     * Enhanced cookie retrieval with caching
     */
    getCookie(name) {
        if (!this.cookieCache) {
            this.cookieCache = new Map();
            if (document.cookie) {
                document.cookie.split(';').forEach(cookie => {
                    const [key, value] = cookie.trim().split('=');
                    if (key && value) {
                        this.cookieCache.set(key, decodeURIComponent(value));
                    }
                });
            }
        }
        return this.cookieCache.get(name) || null;
    }

    /**
     * Improved element resolution with error handling
     */
    resolveElementArray(element, query) {
        try {
            if (!element || typeof element.matches !== 'function') {
                console.warn('Invalid element provided to resolveElementArray');
                return [];
            }
            return element.matches(query) ? [element] : Array.from(element.querySelectorAll(query));
        } catch (error) {
            console.error('Error resolving element array:', error);
            return [];
        }
    }

    /**
     * Enhanced script element finder with validation
     */
    findScriptElement(element, scriptId) {
        const selector = `#${scriptId}-ck-editor-5-upload-url`;
        const scriptElement = element.querySelector(selector);
        
        if (!scriptElement) {
            throw new Error(`Script element not found: ${selector}`);
        }
        
        return scriptElement;
    }

    /**
     * Extract and validate configuration from script elements
     */
    extractEditorConfig(element, scriptId) {
        try {
            const scriptElement = this.findScriptElement(element, scriptId);
            
            const uploadUrl = scriptElement.getAttribute('data-upload-url');
            const uploadFileTypes = JSON.parse(scriptElement.getAttribute('data-upload-file-types') || '[]');
            const csrfCookieName = scriptElement.getAttribute('data-csrf_cookie_name');
            
            if (!uploadUrl || !csrfCookieName) {
                throw new Error('Missing required configuration attributes');
            }
            
            const configElement = element.querySelector(`#${scriptId}-span`);
            if (!configElement) {
                throw new Error(`Configuration element not found: #${scriptId}-span`);
            }
            
            const config = JSON.parse(configElement.textContent, (key, value) => {
                if (typeof value === 'string') {
                    const match = value.match(/^\/(.+?)\/([gimuy]*)$/);
                    if (match) {
                        try {
                            return new RegExp(match[1], match[2]);
                        } catch (regexError) {
                            console.warn('Invalid regex pattern:', value);
                            return value;
                        }
                    }
                }
                return value;
            });
            
            // Enhanced configuration
            config.simpleUpload = {
                uploadUrl,
                headers: {
                    'X-CSRFToken': this.getCookie(csrfCookieName),
                },
            };
            
            config.fileUploader = {
                fileTypes: uploadFileTypes
            };
            
            config.licenseKey = 'GPL';
            
            return config;
        } catch (error) {
            console.error(`Error extracting config for ${scriptId}:`, error);
            throw error;
        }
    }

    /**
     * Clean up adjacent empty text nodes
     */
    cleanupTextNodes(editorEl) {
        const nextSibling = editorEl.nextSibling;
        if (nextSibling && 
            nextSibling.nodeType === Node.TEXT_NODE && 
            nextSibling.textContent.trim() === '') {
            nextSibling.remove();
        }
    }

    /**
     * Setup label styling
     */
    setupLabelStyling(element, editorId) {
        const labelElement = element.querySelector(`[for$="${editorId}"]`);
        if (labelElement) {
            labelElement.style.float = 'none';
        }
    }

    /**
     * Setup word count display
     */
    setupWordCount(editor, element, scriptId) {
        if (editor.plugins.has('WordCount')) {
            try {
                const wordCountPlugin = editor.plugins.get('WordCount');
                const wordCountWrapper = element.querySelector(`#${scriptId}-word-count`);
                
                if (wordCountWrapper) {
                    wordCountWrapper.innerHTML = '';
                    wordCountWrapper.appendChild(wordCountPlugin.wordCountContainer);
                }
            } catch (error) {
                console.error('Error setting up word count:', error);
            }
        }
    }

    /**
     * Create individual editor with enhanced error handling
     */
    async createEditor(editorEl, element = document.body) {
        const editorId = editorEl.id;
        const scriptId = `${editorId}_script`;
        
        try {
            // Skip if already processed or is template
            if (editorId.includes('__prefix__') || 
                editorEl.getAttribute('data-processed') === '1') {
                return;
            }
            
            // Cleanup and setup
            this.cleanupTextNodes(editorEl);
            this.setupLabelStyling(element, editorId);
            
            // Extract configuration
            const config = this.extractEditorConfig(element, scriptId);
            
            // Create editor
            const editor = await ClassicEditor.create(editorEl, config);
            
            // Setup data binding
            const textarea = document.querySelector(`#${editorId}`);
            if (textarea) {
                const updateTextarea = () => {
                    textarea.value = editor.getData();
                };
                
                // Debounced update for better performance
                let updateTimeout;
                editor.model.document.on('change:data', () => {
                    clearTimeout(updateTimeout);
                    updateTimeout = setTimeout(updateTextarea, 100);
                });
            }
            
            // Setup word count
            this.setupWordCount(editor, element, scriptId);
            
            // Store editor
            this.editors.set(editorId, editor);
            
            // Execute callback if registered
            const callback = this.callbacks.get(editorId);
            if (callback && typeof callback === 'function') {
                try {
                    callback(editor);
                } catch (callbackError) {
                    console.error(`Error executing callback for ${editorId}:`, callbackError);
                }
            }
            
            // Mark as processed
            editorEl.setAttribute('data-processed', '1');
            
            console.log(`Editor ${editorId} created successfully`);
            
        } catch (error) {
            console.error(`Failed to create editor ${editorId}:`, error);
            // Mark as processed to prevent retry loops
            editorEl.setAttribute('data-processed', '1');
        }
    }

    /**
     * Create all editors within an element
     */
    async createEditors(element = document.body) {
        const allEditors = this.resolveElementArray(element, '.django_ckeditor_5');
        
        if (allEditors.length === 0) {
            return;
        }
        
        console.log(`Creating ${allEditors.length} editors`);
        
        // Process editors in parallel with concurrency limit
        const concurrencyLimit = 3;
        const promises = [];
        
        for (let i = 0; i < allEditors.length; i += concurrencyLimit) {
            const batch = allEditors.slice(i, i + concurrencyLimit);
            const batchPromises = batch.map(editorEl => this.createEditor(editorEl, element));
            
            promises.push(Promise.allSettled(batchPromises));
        }
        
        await Promise.all(promises);
        
        // Update global reference
        window.editors = this.editors;
    }

    /**
     * Enhanced mutation filtering
     */
    getAddedNodes(mutations) {
        const addedNodes = [];
        
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    addedNodes.push(node);
                }
            }
        }
        
        return addedNodes;
    }

    /**
     * Handle mutations with throttling
     */
    handleMutations(mutations) {
        if (this.mutationTimeout) {
            clearTimeout(this.mutationTimeout);
        }
        
        this.mutationTimeout = setTimeout(() => {
            const addedNodes = this.getAddedNodes(mutations);
            
            addedNodes.forEach(node => {
                this.createEditors(node);
            });
        }, 50); // Throttle to 50ms
    }

    /**
     * Handle Django formset additions
     */
    handleFormsetAdded() {
        console.log('Formset added, creating new editors');
        this.createEditors();
    }

    /**
     * Register callback for editor creation
     */
    registerCallback(id, callback) {
        if (typeof callback !== 'function') {
            console.warn(`Invalid callback provided for ${id}`);
            return;
        }
        
        this.callbacks.set(id, callback);
        console.log(`Callback registered for ${id}`);
    }

    /**
     * Unregister callback
     */
    unregisterCallback(id) {
        this.callbacks.delete(id);
        console.log(`Callback unregistered for ${id}`);
    }

    /**
     * Setup mutation observer
     */
    setupMutationObserver() {
        if (this.observer) {
            this.observer.disconnect();
        }
        
        this.observer = new MutationObserver(this.handleMutations);
        
        const observerOptions = {
            childList: true,
            subtree: true,
        };
        
        this.observer.observe(document.body, observerOptions);
        console.log('MutationObserver initialized');
    }

    /**
     * Setup Django formset integration
     */
    setupDjangoIntegration() {
        if (typeof django === 'object' && django.jQuery) {
            django.jQuery(document).on('formset:added', this.handleFormsetAdded);
            console.log('Django formset integration enabled');
        }
    }

    /**
     * Cleanup method for proper resource disposal
     */
    cleanup() {
        // Clear timeouts
        if (this.mutationTimeout) {
            clearTimeout(this.mutationTimeout);
        }
        
        // Disconnect observer
        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }
        
        // Destroy all editors
        this.editors.forEach((editor, id) => {
            try {
                editor.destroy();
                console.log(`Editor ${id} destroyed`);
            } catch (error) {
                console.error(`Error destroying editor ${id}:`, error);
            }
        });
        
        // Clear collections
        this.editors.clear();
        this.callbacks.clear();
        
        // Clear cookie cache
        this.cookieCache = null;
        
        console.log('CKEditor manager cleanup completed');
    }

    /**
     * Initialize the manager
     */
    async initialize() {
        if (this.isInitialized) {
            console.warn('CKEditor manager already initialized');
            return;
        }
        
        console.log('Initializing CKEditor manager');
        
        try {
            // Create initial editors
            await this.createEditors();
            
            // Setup observers and integrations
            this.setupDjangoIntegration();
            this.setupMutationObserver();
            
            this.isInitialized = true;
            console.log('CKEditor manager initialized successfully');
            
        } catch (error) {
            console.error('Failed to initialize CKEditor manager:', error);
            throw error;
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const manager = new CKEditorManager();
    manager.initialize().catch(error => {
        console.error('CKEditor initialization failed:', error);
    });
    
    // Expose manager for debugging
    window.ckeditorManager = manager;
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
        manager.cleanup();
    });
});

// Handle hot module replacement for development
if (module.hot) {
    module.hot.accept(() => {
        console.log('Hot module replacement detected');
        if (window.ckeditorManager) {
            window.ckeditorManager.cleanup();
        }
    });
}