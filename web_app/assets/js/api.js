/**
 * Determines the API base URL.
 * Prefers `window.API_BASE_URL` (set via a config script),
 * otherwise defaults to the current window's origin.
 */
function getApiBaseUrl() {
    return window.API_BASE_URL || window.location.origin;
}

const API_BASE_URL = getApiBaseUrl();

/** API Client for My Kanha Backend */
class KanhaAPI {
    constructor() {
        this.baseUrl = API_BASE_URL;
    }

    /**
     * Retrieves the JWT token from local storage.
     * @returns {string|null} The JWT token if found, otherwise null.
     */
    getToken() {
        // Support both keys to avoid mismatch between frontend and backend
        return (
            localStorage.getItem('authToken') ||
            localStorage.getItem('jwt_token') ||
            null
        );
    }

    /**
     * Generic fetch wrapper to include authorization headers.
     * @param {string} endpoint - The API endpoint relative to baseUrl.
     * @param {Object} options - Fetch options (method, headers, body, etc.).
     * @returns {Promise<Response>}
     */
    async _fetch(endpoint, options = {}) {
        const token = this.getToken();
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        if (token) headers['Authorization'] = `Bearer ${token}`;

        const response = await fetch(`${this.baseUrl}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const errorBody = await response.json().catch(() => ({ detail: `HTTP error! status: ${response.status}` }));
            throw new Error(errorBody.detail || `HTTP error! status: ${response.status}`);
        }

        return response;
    }

    /**
     * Send a chat message and get Krishna's response
     * @param {string} message - User's message
     * @param {string} language - Language preference ('english', 'hindi', or 'auto')
     * @param {number} topK - Number of verses to retrieve
     * @param {Array} conversationHistory - Previous messages for context
     * @returns {Promise<Object>} - Chat response with sources
     */
    async sendMessage(message, language = 'english', topK = 5, conversationHistory = []) {
        const response = await this._fetch('/chat/', {
            method: 'POST',
            body: JSON.stringify({
                message,
                language,
                top_k: topK,
                conversation_history: conversationHistory,
            }),
        });
        return response.json();
    }

    /**
     * Send a chat message with streaming response
     * @param {string} message - User's message
     * @param {string} language - Language preference
     * @param {number} topK - Number of verses to retrieve
     * @param {Function} onChunk - Callback for each text chunk
     * @param {Function} onComplete - Callback when streaming completes
     * @param {Function} onError - Callback for errors
     */
    async sendMessageStream(message, language = 'english', topK = 5, onChunk, onComplete, onError) {
        try {
            const response = await this._fetch('/chat/stream', {
                method: 'POST',
                body: JSON.stringify({ message, language, top_k: topK }),
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let sources = [];

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.content && !data.is_complete) onChunk(data.content);
                            if (data.is_complete && data.sources) sources = data.sources;
                        } catch (e) {
                            console.warn('Failed to parse SSE data:', line);
                        }
                    }
                }
            }

            onComplete(sources);
        } catch (error) {
            onError(error);
        }
    }

    /**
     * Check backend health status
     * @returns {Promise<Object>} - Health status
     */
    async checkHealth() {
        const response = await this._fetch('/health/chroma');
        return response.json();
    }

    /**
     * Check if backend is reachable
     * @returns {Promise<boolean>}
     */
    async isBackendReachable() {
        try {
            await this._fetch('/health', {
                method: 'GET',
                signal: AbortSignal.timeout(5000),
            });
            return true;
        } catch (error) {
            console.error('Backend not reachable:', error);
            return false;
        }
    }
}

// Create a shared instance for other scripts
window.kanhaAPI = new KanhaAPI();


