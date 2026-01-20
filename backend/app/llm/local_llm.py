"""
Local LLM
Integration with Ollama or other local LLM providers.
"""

from typing import Optional, Dict, Any, AsyncGenerator
import httpx

from app.config import settings
from app.logger import logger


class OllamaClient:
    """Client for interacting with Ollama API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.LLM_MODEL
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: The user prompt
            system: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.LLM_MAX_TOKENS

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                return data.get("response", "")

        except httpx.TimeoutException:
            logger.error("LLM request timed out")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = None,
        max_tokens: int = None,
    ) -> AsyncGenerator[str, None]:
        """
        Generate a streaming response from the LLM.

        Yields:
            Text chunks as they are generated
        """
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.LLM_MAX_TOKENS

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        if system:
            payload["system"] = system

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/generate",
                    json=payload,
                ) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if line:
                            import json
                            data = json.loads(line)
                            if chunk := data.get("response"):
                                yield chunk

                            if data.get("done"):
                                break

        except Exception as e:
            logger.error(f"LLM streaming error: {e}")
            raise

    async def chat(
        self,
        messages: list,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        """
        Chat completion with message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        if temperature is None:
            temperature = settings.LLM_TEMPERATURE
        if max_tokens is None:
            max_tokens = settings.LLM_MAX_TOKENS

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )
                response.raise_for_status()

                data = response.json()
                return data.get("message", {}).get("content", "")

        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            raise


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_llm_client() -> OllamaClient:
    """Get or create the Ollama client instance."""
    global _ollama_client

    if _ollama_client is None:
        _ollama_client = OllamaClient()

    return _ollama_client


async def check_llm_health() -> bool:
    """Check if the LLM service is available."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"LLM health check failed: {e}")
        return False


async def list_available_models() -> list:
    """List available models in Ollama."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()

            data = response.json()
            return [model["name"] for model in data.get("models", [])]

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return []
