"""
ChromaDB Initialization Module
Auto-loads and indexes Gita data on backend startup
"""

import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_CLEANED_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'gita_master.json'
VECTOR_DB_PATH = PROJECT_ROOT / 'vector_db' / 'chroma'
INIT_FLAG_FILE = VECTOR_DB_PATH / '.initialized'


class ChromaDBInitializer:
    """Initialize and manage ChromaDB on application startup"""
    
    _initialized = False
    _retriever = None
    
    @classmethod
    def initialize(cls) -> bool:
        """
        Initialize ChromaDB on first startup
        
        Returns:
            True if successfully initialized or already initialized
        """
        if cls._initialized:
            logger.debug("ChromaDB already initialized")
            return True
        
        try:
            # Check if index already exists
            if INIT_FLAG_FILE.exists():
                logger.info("ChromaDB index already exists, skipping initialization")
                cls._initialized = True
                return True
            
            # Check if raw data exists
            if not DATA_CLEANED_PATH.exists():
                logger.error(f"Data file not found: {DATA_CLEANED_PATH}")
                logger.error("Please run 'python data/scripts/embed_and_index.py' first")
                return False
            
            # Create embeddings and index
            logger.info("Starting ChromaDB initialization...")
            from data.scripts.embed_and_index import GitaEmbedder
            
            embedder = GitaEmbedder()
            embedder.run()
            
            # Mark as initialized
            VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
            INIT_FLAG_FILE.touch()
            
            logger.info("✓ ChromaDB initialization complete")
            cls._initialized = True
            return True
        
        except ImportError as e:
            logger.error(f"Missing dependency: {str(e)}")
            logger.error("Please install required packages: pip install sentence-transformers chromadb")
            return False
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def get_retriever(cls):
        """Get initialized retriever instance"""
        if not cls._initialized:
            cls.initialize()
        
        if cls._retriever is None:
            from app.rag.retriever import GitaRetriever
            cls._retriever = GitaRetriever()
        
        return cls._retriever
    
    @classmethod
    def check_health(cls) -> dict:
        """Check ChromaDB health status"""
        try:
            retriever = cls.get_retriever()
            return retriever.health_check()
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }


def startup_event() -> None:
    """FastAPI startup event handler"""
    logger.info("Running FastAPI startup tasks...")
    
    # Initialize ChromaDB
    if ChromaDBInitializer.initialize():
        logger.info("✓ Backend initialized successfully")
    else:
        logger.warning("⚠ ChromaDB initialization failed - some features may not work")


def health_check() -> dict:
    """Health check endpoint"""
    return ChromaDBInitializer.check_health()
- Singleton pattern for ChromaDB client
- Lazy loading of embedding model
- Health checks and statistics
- Graceful error handling

Usage:
    from app.rag.init_chromadb import get_chroma_collection, get_embedding_model

    collection = get_chroma_collection()
    model = get_embedding_model()
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent.parent  # My_Kanha_Project
VECTOR_DB_DIR = BASE_DIR / "vector_db" / "chroma"
COLLECTION_NAME = "gita_verses"
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Global instances (singleton pattern)
_chroma_client = None
_chroma_collection = None
_embedding_model = None
_initialized = False


class ChromaDBNotInitializedError(Exception):
    """Raised when ChromaDB is accessed before initialization."""
    pass


class ChromaDBEmptyError(Exception):
    """Raised when ChromaDB collection is empty."""
    pass


def initialize_chromadb(
    persist_dir: Optional[Path] = None,
    collection_name: str = COLLECTION_NAME
) -> Tuple[Any, Any]:
    """
    Initialize ChromaDB client and collection.

    Args:
        persist_dir: Optional custom directory for ChromaDB
        collection_name: Name of the collection to use

    Returns:
        Tuple of (client, collection)

    Raises:
        ImportError: If chromadb is not installed
        Exception: If initialization fails
    """
    global _chroma_client, _chroma_collection, _initialized

    if _initialized and _chroma_collection is not None:
        return _chroma_client, _chroma_collection

    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError as e:
        logger.error("chromadb not installed. Install with: pip install chromadb")
        raise ImportError("chromadb package is required") from e

    persist_path = persist_dir or VECTOR_DB_DIR

    # Ensure directory exists
    persist_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing ChromaDB from {persist_path}")

    try:
        # Create persistent client
        _chroma_client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False,  # Prevent accidental resets in production
            )
        )

        # Get existing collection
        try:
            _chroma_collection = _chroma_client.get_collection(
                name=collection_name
            )
            doc_count = _chroma_collection.count()
            logger.info(f"Loaded collection '{collection_name}' with {doc_count} documents")

            if doc_count == 0:
                logger.warning(f"Collection '{collection_name}' is empty. Run embed_and_index.py first.")

        except Exception:
            # Collection doesn't exist - create it
            logger.warning(f"Collection '{collection_name}' not found. Creating new collection.")
            _chroma_collection = _chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.warning("Collection is empty. Run data/scripts/embed_and_index.py to populate.")

        _initialized = True
        return _chroma_client, _chroma_collection

    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB: {e}")
        raise


def initialize_embedding_model(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    device: str = "cpu"
) -> Any:
    """
    Initialize the sentence transformer embedding model.

    Args:
        model_name: Name of the model to load
        device: Device to use (cpu/cuda)

    Returns:
        SentenceTransformer model instance

    Raises:
        ImportError: If sentence-transformers is not installed
    """
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
        raise ImportError("sentence-transformers package is required") from e

    logger.info(f"Loading embedding model: {model_name} on {device}")

    try:
        _embedding_model = SentenceTransformer(model_name, device=device)
        logger.info(f"Embedding model loaded. Dimension: {_embedding_model.get_sentence_embedding_dimension()}")
        return _embedding_model

    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        raise


@lru_cache(maxsize=1)
def get_chroma_collection():
    """
    Get the ChromaDB collection (with lazy initialization).

    Returns:
        ChromaDB collection object

    Raises:
        ChromaDBNotInitializedError: If initialization fails
    """
    global _chroma_collection

    if _chroma_collection is None:
        try:
            _, _chroma_collection = initialize_chromadb()
        except Exception as e:
            raise ChromaDBNotInitializedError(f"Failed to initialize ChromaDB: {e}")

    return _chroma_collection


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Get the embedding model (with lazy initialization).

    Returns:
        SentenceTransformer model instance
    """
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = initialize_embedding_model()

    return _embedding_model


def get_collection_stats() -> dict:
    """
    Get statistics about the ChromaDB collection.

    Returns:
        Dictionary with collection statistics
    """
    try:
        collection = get_chroma_collection()
        count = collection.count()

        # Get sample to check metadata
        sample = collection.peek(limit=1)
        metadata_fields = list(sample['metadatas'][0].keys()) if sample['metadatas'] else []

        return {
            "status": "healthy",
            "collection_name": COLLECTION_NAME,
            "document_count": count,
            "persist_directory": str(VECTOR_DB_DIR),
            "metadata_fields": metadata_fields,
            "embedding_model": DEFAULT_EMBEDDING_MODEL,
            "embedding_dimension": EMBEDDING_DIMENSION
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "collection_name": COLLECTION_NAME,
            "document_count": 0
        }


def health_check() -> Tuple[bool, str]:
    """
    Perform health check on ChromaDB.

    Returns:
        Tuple of (is_healthy, message)
    """
    try:
        collection = get_chroma_collection()
        count = collection.count()

        if count == 0:
            return False, "ChromaDB collection is empty. Run embed_and_index.py to populate."

        # Try a simple query
        model = get_embedding_model()
        test_embedding = model.encode(["test query"])[0].tolist()

        result = collection.query(
            query_embeddings=[test_embedding],
            n_results=1
        )

        if result['ids'] and result['ids'][0]:
            return True, f"ChromaDB healthy with {count} documents"
        else:
            return False, "ChromaDB query returned no results"

    except ChromaDBNotInitializedError as e:
        return False, f"ChromaDB not initialized: {e}"
    except Exception as e:
        return False, f"ChromaDB health check failed: {e}"


def query_similar(
    query_text: str,
    n_results: int = 5,
    where_filter: Optional[dict] = None
) -> dict:
    """
    Query ChromaDB for similar verses.

    Args:
        query_text: Text to search for
        n_results: Number of results to return
        where_filter: Optional metadata filter

    Returns:
        Query results from ChromaDB
    """
    collection = get_chroma_collection()
    model = get_embedding_model()

    # Generate query embedding
    query_embedding = model.encode([query_text])[0].tolist()

    # Build query params
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": n_results,
        "include": ["documents", "metadatas", "distances"]
    }

    if where_filter:
        query_params["where"] = where_filter

    return collection.query(**query_params)


def shutdown():
    """
    Gracefully shutdown ChromaDB connection.
    Called during application shutdown.
    """
    global _chroma_client, _chroma_collection, _embedding_model, _initialized

    logger.info("Shutting down ChromaDB connection...")

    _chroma_collection = None
    _chroma_client = None
    _embedding_model = None
    _initialized = False

    # Clear LRU caches
    get_chroma_collection.cache_clear()
    get_embedding_model.cache_clear()

    logger.info("ChromaDB shutdown complete")


# ============ FastAPI Lifespan Integration ============

async def startup_event():
    """
    FastAPI startup event handler.
    Initialize ChromaDB and embedding model.
    """
    logger.info("Starting ChromaDB initialization...")

    try:
        # Initialize ChromaDB
        initialize_chromadb()

        # Initialize embedding model
        initialize_embedding_model()

        # Health check
        is_healthy, message = health_check()
        if is_healthy:
            logger.info(f"ChromaDB startup successful: {message}")
        else:
            logger.warning(f"ChromaDB startup warning: {message}")

    except Exception as e:
        logger.error(f"ChromaDB startup failed: {e}")
        # Don't raise - allow app to start but RAG will be unavailable


async def shutdown_event():
    """
    FastAPI shutdown event handler.
    """
    shutdown()


# ============ CLI for Testing ============

def main():
    """Command-line interface for testing ChromaDB initialization."""
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description="Test ChromaDB initialization")
    parser.add_argument('--stats', action='store_true', help='Show collection statistics')
    parser.add_argument('--health', action='store_true', help='Run health check')
    parser.add_argument('--query', type=str, help='Test query')

    args = parser.parse_args()

    print("=" * 60)
    print("CHROMADB INITIALIZATION TEST")
    print("=" * 60)

    try:
        # Initialize
        print("\nInitializing ChromaDB...")
        initialize_chromadb()
        print("ChromaDB initialized successfully!")

        print("\nLoading embedding model...")
        initialize_embedding_model()
        print("Embedding model loaded!")

        if args.stats:
            print("\n--- Collection Statistics ---")
            stats = get_collection_stats()
            for key, value in stats.items():
                print(f"  {key}: {value}")

        if args.health:
            print("\n--- Health Check ---")
            is_healthy, message = health_check()
            status = "[HEALTHY]" if is_healthy else "[UNHEALTHY]"
            print(f"  {status} {message}")

        if args.query:
            print(f"\n--- Test Query: '{args.query}' ---")
            results = query_similar(args.query, n_results=3)

            if results['ids'] and results['ids'][0]:
                for i, (doc_id, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    similarity = 1 / (1 + distance)
                    print(f"\n  [{i+1}] {doc_id}")
                    print(f"      Chapter {metadata.get('chapter')}, Verse {metadata.get('verse')}")
                    print(f"      Similarity: {similarity:.3f}")
                    english = metadata.get('english', '')[:100]
                    print(f"      English: {english}...")
            else:
                print("  No results found")

        # Default: show basic stats and health
        if not (args.stats or args.health or args.query):
            stats = get_collection_stats()
            is_healthy, message = health_check()

            print(f"\n  Collection: {stats['collection_name']}")
            print(f"  Documents: {stats['document_count']}")
            print(f"  Status: {message}")

        print("\n" + "=" * 60)
        print("TEST COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
