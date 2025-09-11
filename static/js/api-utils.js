/**
 * API Utilities for Django CSRF and common AJAX operations
 */

// Get CSRF token from meta tag or form
function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrfToken) {
        return csrfToken.value;
    }
    
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    
    return null;
}

// Enhanced fetch with CSRF token and error handling
async function secureApiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    // Add CSRF token for POST, PUT, PATCH, DELETE requests
    if (options.method && !['GET', 'HEAD', 'OPTIONS'].includes(options.method.toUpperCase())) {
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    // Merge options
    const finalOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            // Handle HTTP errors
            const errorMessage = `HTTP Error ${response.status}: ${response.statusText}`;
            console.error('API Error:', errorMessage);
            
            // Try to get error details from response
            try {
                const errorData = await response.json();
                throw new Error(errorData.error || errorData.detail || errorMessage);
            } catch {
                throw new Error(errorMessage);
            }
        }
        
        return await response.json();
    } catch (error) {
        console.error('API Call Failed:', error);
        throw error;
    }
}

// Show user-friendly error messages
function showApiError(error, container = null) {
    const message = error.message || 'Ha ocurrido un error inesperado';
    
    if (container) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="bi bi-exclamation-triangle"></i>
                ${message}
            </div>
        `;
    } else {
        // Fallback to console if no container
        console.error('API Error:', message);
    }
}

// Generic loading state handler
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.disabled = true;
        const originalText = element.textContent;
        element.setAttribute('data-original-text', originalText);
        element.innerHTML = '<i class="spinner-border spinner-border-sm me-2"></i>Cargando...';
    } else {
        element.disabled = false;
        const originalText = element.getAttribute('data-original-text');
        if (originalText) {
            element.textContent = originalText;
            element.removeAttribute('data-original-text');
        }
    }
}