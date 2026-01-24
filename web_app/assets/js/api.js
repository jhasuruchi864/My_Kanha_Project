/**
 * API Client for My Kanha Backend
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * API Client class for making requests to the backend
 */
class KanhaAPI {
    constructor(baseUrl = API_BASE_URL) {
        this.baseUrl = baseUrl;
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
        const response = await fetch(`${this.baseUrl}/chat/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                language: language,
                top_k: topK,
                conversation_history: conversationHistory
            })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP error! status: ${response.status}`);
        }

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
            const response = await fetch(`${this.baseUrl}/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    language: language,
                    top_k: topK
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let sources = [];

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.content && !data.is_complete) {
                                onChunk(data.content);
                            }
                            if (data.is_complete && data.sources) {
                                sources = data.sources;
                            }
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
        const response = await fetch(`${this.baseUrl}/health/chroma`);
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        return response.json();
    }

    /**
     * Check if backend is reachable
     * @returns {Promise<boolean>}
     */
    async isBackendReachable() {
        try {
            const response = await fetch(`${this.baseUrl}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000) // 5 second timeout
            });
            return response.ok;
        } catch (error) {
            console.error('Backend not reachable:', error);
            return false;
        }
    }
}

// Create global API instance
const kanhaAPI = new KanhaAPI();
