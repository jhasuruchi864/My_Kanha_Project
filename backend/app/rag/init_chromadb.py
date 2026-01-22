"""
ChromaDB Initialization Module
Auto-loads and indexes Gita data on backend startup
"""

import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_CLEANED_PATH = PROJECT_ROOT / 'data' / 'cleaned' / 'gita_master.json'
VECTOR_DB_PATH = PROJECT_ROOT / 'vector_db' / 'chroma'
INIT_FLAG_FILE = VECTOR_DB_PATH / '.initialized'
LAST_INDEX_FILE = VECTOR_DB_PATH / '.last_index'


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

            # Import the embedding functions
            import sys
            scripts_path = PROJECT_ROOT / 'data' / 'scripts'
            if str(scripts_path) not in sys.path:
                sys.path.insert(0, str(scripts_path))

            from embed_and_index import (
                load_master_data,
                initialize_chroma,
                load_embedding_model,
                prepare_documents,
                generate_embeddings,
                index_documents,
                MASTER_FILE,
                VECTOR_DB_DIR,
                DEFAULT_MODEL,
                DEFAULT_DEVICE,
            )

            # Run the indexing pipeline
            data = load_master_data(MASTER_FILE)
            collection, client = initialize_chroma(VECTOR_DB_DIR, reset=False)
            model = load_embedding_model(DEFAULT_MODEL, DEFAULT_DEVICE)
            documents = prepare_documents(data)
            texts = [doc['text'] for doc in documents]
            embeddings = generate_embeddings(texts, model, batch_size=32)
            index_documents(collection, documents, embeddings)

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


def get_last_index_time() -> Optional[str]:
    """Get the timestamp of last successful index."""
    try:
        if LAST_INDEX_FILE.exists():
            return LAST_INDEX_FILE.read_text().strip()
        return None
    except Exception as e:
        logger.error(f"Failed to read last index time: {e}")
        return None


def set_last_index_time() -> str:
    """Set the last index time to now and return the timestamp."""
    timestamp = datetime.now().isoformat()
    try:
        VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
        LAST_INDEX_FILE.write_text(timestamp)
    except Exception as e:
        logger.error(f"Failed to write last index time: {e}")
    return timestamp


def reindex(reset: bool = True) -> Dict[str, Any]:
    """
    Reindex the Gita data into ChromaDB.

    Args:
        reset: If True, clear existing collection before indexing

    Returns:
        Dict with indexing results (docs_indexed, duration, model, persist_dir)
    """
    from app.config import settings

    start_time = time.time()
    result = {
        "success": False,
        "docs_indexed": 0,
        "duration_seconds": 0,
        "embedding_model": settings.EMBEDDING_MODEL,
        "persist_dir": str(VECTOR_DB_PATH),
        "last_index_time": None,
        "error": None,
    }

    try:
        # Check if raw data exists
        if not DATA_CLEANED_PATH.exists():
            result["error"] = f"Data file not found: {DATA_CLEANED_PATH}"
            logger.error(result["error"])
            return result

        # Import and run embedder functions
        logger.info(f"Starting reindex (reset={reset})...")

        # Import the embedding functions
        import sys
        scripts_path = PROJECT_ROOT / 'data' / 'scripts'
        if str(scripts_path) not in sys.path:
            sys.path.insert(0, str(scripts_path))

        from embed_and_index import (
            load_master_data,
            initialize_chroma,
            load_embedding_model,
            prepare_documents,
            generate_embeddings,
            index_documents,
            MASTER_FILE,
            VECTOR_DB_DIR,
        )

        # Step 1: Load data
        data = load_master_data(MASTER_FILE)

        # Step 2: Initialize ChromaDB
        collection, client = initialize_chroma(VECTOR_DB_DIR, reset=reset)

        # Step 3: Load embedding model
        model = load_embedding_model(settings.EMBEDDING_MODEL, settings.EMBEDDING_DEVICE)

        # Step 4: Prepare documents
        documents = prepare_documents(data)

        if not documents:
            result["error"] = "No documents to index"
            return result

        # Step 5: Generate embeddings
        texts = [doc['text'] for doc in documents]
        embeddings = generate_embeddings(texts, model, batch_size=32)

        # Step 6: Index to ChromaDB
        index_documents(collection, documents, embeddings)

        # Get final count
        docs_count = collection.count()

        # Update tracking files
        INIT_FLAG_FILE.touch()
        last_index_time = set_last_index_time()

        # Reset initializer state so it picks up fresh data
        ChromaDBInitializer._initialized = False
        ChromaDBInitializer._retriever = None

        duration = time.time() - start_time

        result.update({
            "success": True,
            "docs_indexed": docs_count,
            "duration_seconds": round(duration, 2),
            "last_index_time": last_index_time,
        })

        logger.info(f"Reindex complete: {docs_count} docs in {duration:.2f}s")
        return result

    except ImportError as e:
        result["error"] = f"Missing dependency: {str(e)}"
        logger.error(result["error"])
        return result
    except Exception as e:
        result["error"] = str(e)
        result["duration_seconds"] = round(time.time() - start_time, 2)
        logger.error(f"Reindex failed: {e}", exc_info=True)
        return result


def get_collection_stats() -> Dict[str, Any]:
    """
    Get ChromaDB collection statistics.

    Returns:
        Dict with collection health and metadata
    """
    from app.config import settings

    stats = {
        "status": "unhealthy",
        "total_verses_indexed": 0,
        "vector_db_path": str(VECTOR_DB_PATH),
        "collection_name": "gita_verses",
        "last_index_time": get_last_index_time(),
        "embedding_model": settings.EMBEDDING_MODEL,
        "ollama_model": settings.LLM_MODEL,
        "error": None,
    }

    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(VECTOR_DB_PATH))
        collection = client.get_collection("gita_verses")

        stats["status"] = "healthy"
        stats["total_verses_indexed"] = collection.count()

    except Exception as e:
        stats["error"] = str(e)
        logger.error(f"Failed to get collection stats: {e}")

    return stats
