"""
Vector Store
ChromaDB wrapper for vector storage and retrieval.
"""

from typing import Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import settings
from app.logger import logger
from app.core.constants import CHROMA_COLLECTION_NAME


# Global ChromaDB client and collection
_chroma_client: Optional[chromadb.Client] = None
_collection: Optional[chromadb.Collection] = None


def initialize_chroma():
    """Initialize ChromaDB client and collection."""
    global _chroma_client, _collection

    persist_dir = Path(settings.CHROMA_PERSIST_DIR)
    persist_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing ChromaDB at {persist_dir}")

    try:
        _chroma_client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # Get or create collection
        _collection = _chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Use cosine similarity
        )

        logger.info(f"ChromaDB initialized. Collection '{CHROMA_COLLECTION_NAME}' ready.")
        logger.info(f"Current document count: {_collection.count()}")

    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


def get_vector_store() -> Optional[chromadb.Collection]:
    """Get the ChromaDB collection."""
    global _collection

    if _collection is None:
        logger.warning("Vector store not initialized. Call initialize_chroma() first.")

    return _collection


def get_client() -> Optional[chromadb.Client]:
    """Get the ChromaDB client."""
    return _chroma_client


def reset_collection():
    """Reset (delete and recreate) the collection."""
    global _chroma_client, _collection

    if _chroma_client is None:
        raise RuntimeError("ChromaDB client not initialized")

    try:
        # Delete existing collection
        _chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
        logger.info(f"Deleted collection '{CHROMA_COLLECTION_NAME}'")

        # Recreate collection
        _collection = _chroma_client.create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"Recreated collection '{CHROMA_COLLECTION_NAME}'")

    except Exception as e:
        logger.error(f"Failed to reset collection: {e}")
        raise


def get_collection_stats() -> dict:
    """Get statistics about the collection."""
    if _collection is None:
        return {"status": "not_initialized"}

    return {
        "status": "ready",
        "name": CHROMA_COLLECTION_NAME,
        "count": _collection.count(),
        "persist_directory": settings.CHROMA_PERSIST_DIR,
    }
