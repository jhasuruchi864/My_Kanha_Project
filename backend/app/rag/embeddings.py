"""
Embeddings
Embedding model configuration and utilities.
"""

from typing import List, Callable
from functools import lru_cache

from app.config import settings
from app.logger import logger


# Global embedding model instance
_embedding_model = None


def get_embedding_function() -> Callable[[List[str]], List[List[float]]]:
    """
    Get the embedding function for generating vector embeddings.

    Returns:
        Callable that takes list of texts and returns list of embeddings
    """
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = _load_embedding_model()

    def embed_texts(texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []

        embeddings = _embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

        return embeddings.tolist()

    return embed_texts


def _load_embedding_model():
    """Load the sentence transformer model."""
    try:
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")

        model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE,
        )

        logger.info("Embedding model loaded successfully")
        return model

    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise


@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> tuple:
    """
    Get cached embedding for a single text.

    Uses LRU cache to avoid recomputing embeddings for repeated queries.
    Returns tuple for hashability.
    """
    embedding_fn = get_embedding_function()
    embedding = embedding_fn([text])[0]
    return tuple(embedding)


def get_embedding_dimension() -> int:
    """Get the dimension of the embedding vectors."""
    from app.core.constants import EMBEDDING_DIMENSIONS

    return EMBEDDING_DIMENSIONS.get(
        settings.EMBEDDING_MODEL,
        384  # Default dimension
    )


def compute_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Compute cosine similarity between two embeddings.

    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector

    Returns:
        Cosine similarity score (0 to 1)
    """
    import numpy as np

    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)

    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))
