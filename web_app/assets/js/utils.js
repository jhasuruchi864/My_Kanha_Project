/**
 * Utility functions for My Kanha Web App
 */

/**
 * Format a verse citation for display
 * @param {Object} source - Verse source object
 * @returns {string} - Formatted citation
 */
function formatVerseCitation(source) {
    return `Chapter ${source.chapter}, Verse ${source.verse}`;
}

/**
 * Format similarity score as percentage
 * @param {number} score - Similarity score (0-1)
 * @returns {string} - Formatted percentage
 */
function formatSimilarityScore(score) {
    if (!score) return '';
    return `${Math.round(score * 100)}% relevant`;
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Raw text
 * @returns {string} - Escaped HTML
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Get current timestamp formatted
 * @returns {string} - Formatted time
 */
function getCurrentTime() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Scroll element to bottom smoothly
 * @param {HTMLElement} element - Element to scroll
 */
function scrollToBottom(element) {
    element.scrollTo({
        top: element.scrollHeight,
        behavior: 'smooth'
    });
}

/**
 * Debounce function to limit rapid calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} - Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Store data in localStorage
 * @param {string} key - Storage key
 * @param {any} value - Value to store
 */
function storeLocal(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.warn('localStorage not available:', e);
    }
}

/**
 * Retrieve data from localStorage
 * @param {string} key - Storage key
 * @param {any} defaultValue - Default if not found
 * @returns {any} - Stored value or default
 */
function getLocal(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.warn('localStorage not available:', e);
        return defaultValue;
    }
}

/**
 * Detect if text is likely Hindi (Devanagari script)
 * @param {string} text - Text to check
 * @returns {boolean}
 */
function isHindiText(text) {
    const devanagariPattern = /[\u0900-\u097F]/;
    const devanagariCount = (text.match(/[\u0900-\u097F]/g) || []).length;
    return devanagariCount / text.length > 0.3;
}

/**
 * Truncate text with ellipsis
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated text
 */
function truncateText(text, maxLength = 100) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength).trim() + '...';
}
